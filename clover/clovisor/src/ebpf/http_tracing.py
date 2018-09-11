#!/usr/bin/env python
#
from bcc import BPF
import ctypes as ct
import enum
import getopt
import pyroute2
import socket
import struct
import sys
import time

from BaseHTTPServer import BaseHTTPRequestHandler
from StringIO import StringIO
from httplib import HTTPResponse

global request_dict
global response_dict

class HTTPRequest(BaseHTTPRequestHandler):
    def __init__(self, request_text):
        self.rfile = StringIO(request_text)
        self.raw_requestline = self.rfile.readline()
        self.error_code = self.error_message = None
        self.parse_request()

    def send_error(self, code, message):
        self.error_code = code
        self.error_message = message

class FakeSocket():
    def __init__(self, response_str):
        self._file = StringIO(response_str)
    def makefile(self, *args, **kwargs):
        return self._file

class AppProto(enum.Enum):
    http = 1
    grpc = 2

def print_skb_event(cpu, data, size):
    class SkbEvent(ct.Structure):
        _fields_ =  [ ("offset", ct.c_uint32),
                      ("raw", ct.c_ubyte * (size - ct.sizeof(ct.c_uint32))) ]

    global request_dict
    global response_dict
    str_size = size - ct.sizeof(ct.c_uint32)
    skb_event = ct.cast(data, ct.POINTER(SkbEvent)).contents
    offset = skb_event.offset
    src_ip = bytes(bytearray(skb_event.raw[26:30]))
    dst_ip = bytes(bytearray(skb_event.raw[30:34]))
    src_port = struct.unpack('>H', bytearray(skb_event.raw[34:36]))[0]
    dst_port = struct.unpack('>H', bytearray(skb_event.raw[36:38]))[0]
    body = str(bytearray(skb_event.raw[offset:str_size]))
    if len(body) < 7:
        return
    print('length of body is %d' % len(body))
    print("%-3s %-12s %-12s %-10d %-10d %-10d" %
          (cpu, socket.inet_ntop(socket.AF_INET, src_ip),
          socket.inet_ntop(socket.AF_INET, dst_ip),
          src_port, dst_port, skb_event.offset))
    try:
        request = HTTPRequest(body)

        print request.error_code       # None  (check this first)
        print request.command          # "GET"
        print request.path             # "/who/ken/trust.html"
        print request.request_version  # "HTTP/1.1"
        print len(request.headers)     # 3
        print request.headers.keys()   # ['accept-charset', 'host', 'accept']
        print request.headers['host']  # "cm.bell-labs.com"
        request_dict['src_ip'] = struct.unpack('>I', src_ip)[0]
        request_dict['dst_ip'] = struct.unpack('>I', dst_ip)[0]
        request_dict['src_port'] = src_port
        request_dict['dst_port'] = dst_port
        request_dict['request'] = request
    except:
        print("not a request")

    try:
        source = FakeSocket(body)
        response = HTTPResponse(source)
        response.begin()
        print "status:", response.status
        print "single header:", response.getheader('Content-Type')
        #print "content:", response.read(len(http_response_str))
        response_dict['src_ip'] = struct.unpack('>I', src_ip)[0]
        response_dict['dst_ip'] = struct.unpack('>I', dst_ip)[0]
        response_dict['src_port'] = src_port
        response_dict['dst_port'] = dst_port
        response_dict['response'] = response
    except:
        print("not a response")


def main(argv):
    global request_dict
    global response_dict
    request_dict = {}
    response_dict = {}
    intf_name = None
    port_num = None
    traffic_t = None
    help_str = 'python http_tracing.py -i <interface-name> -p <port-num> -t <traffic type>'
    try:
        opts, args = getopt.getopt(argv, "hi:p:t:", ["intf-name", "port-num", "traffic-type"])
    except getopt.GetoptError:
        print help_str
        sys.exit(1)
    for opt, arg in opts:
        if opt == '-h':
            print help_str
            sys.exit()
        elif opt in ("-i", "--intf-name"):
            intf_name = str(arg)
        elif opt in ("-p", "--port-num"):
            port_num = int(arg)
        elif opt in ("-t", "--traffic-type"):
            traffic_t = str(arg)

    if not intf_name or not port_num or not traffic_t:
        print help_str
        sys.exit(2)

    tt_dict = {}
    for app_p in (AppProto):
        tt_dict[app_p.name] = app_p.value

    print('SKW: tt_dict is %s' % tt_dict)

    if traffic_t not in tt_dict:
        print('%s not supported. Support traffic types are %s' % \
              (traffic_t, tt_dict.keys()))
        sys.exit(3)

    ipr = pyroute2.IPRoute()
    if_idx = ipr.link_lookup(ifname=intf_name)[0]
    try:
        b = BPF(src_file="packet_filter.c", debug=0)
        print('SKW: loaded BPF program')
        fn = b.load_func("handle_ingress", BPF.SCHED_CLS)
        print('SKW: loaded handle_ingress')
        efn = b.load_func("handle_egress", BPF.SCHED_CLS)
        print('SKW: loaded handle_egress')
        tcpdports = b['dports2proto']
        sessions = b.get_table('sessions')

        tcpdports[ct.c_ushort(port_num)] = ct.c_uint(tt_dict[traffic_t])

        ipr.tc("add", "clsact", if_idx)
        ipr.tc("add-filter", "bpf", if_idx, ":1", fd=fn.fd, name=fn.name,
                parent="ffff:fff2", classid=1, direct_action=True)
        ipr.tc("add-filter", "bpf", if_idx, ":1", fd=efn.fd, name=efn.name,
                parent="ffff:fff3", classid=1, direct_action=True)

        b["skb_events"].open_perf_buffer(print_skb_event)
        print('Send HTTP request to %s\n' % intf_name)
        print("%-3s %-12s %-12s %-10s %-10s %-10s" % ("CPU", "SRC IP", "DST IP", "SRC PORT",
                                                      "DST PORT", "OFFSET"))

        while True:
            b.perf_buffer_poll()
            if len(request_dict):
                session_key = sessions.Key(ct.c_uint(request_dict['src_ip']),
                                           ct.c_uint(request_dict['dst_ip']),
                                           ct.c_ushort(request_dict['src_port']),
                                           ct.c_ushort(request_dict['dst_port']))
                '''
                sessions[session_key] = ct.c_float(time.time())
                '''

                print('session table now has')
                for key, val in sessions.items():
                    print('src_ip: %d' % key.src_ip)
                    print('dst_ip: %d' % key.dst_ip)
                    print('src_port : %d' % key.src_port)
                    print('dst_port : %d' % key.dst_port)
                    print('start time: %d' % val.req_time)

                request_dict = {}

            if len(response_dict):
                session_key = sessions.Key(ct.c_uint(response_dict['dst_ip']),
                                           ct.c_uint(response_dict['src_ip']),
                                           ct.c_ushort(response_dict['dst_port']),
                                           ct.c_ushort(response_dict['src_port']))
                print('src_ip: %d' % session_key.src_ip)
                print('dst_ip: %d' % session_key.dst_ip)
                print('src_port : %d' % session_key.src_port)
                print('dst_port : %d' % session_key.dst_port)

                '''
                cur_time = time.time()
                '''
                session = sessions[session_key]

                duration = (session.resp_time - session.req_time) / 1000

                print('Duration: %d' % duration)
                response_dict = {}

    finally:
        ipr.tc("del", "clsact", if_idx)
        print('done')

if __name__ == "__main__":
    main(sys.argv[1:])
