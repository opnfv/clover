# Copyright (c) Authors of Clover
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0

from concurrent import futures
from jinja2 import Template
from urlparse import urlparse
import time
import sys
import grpc
import subprocess
import pickle
import logging
import jmeter_pb2
import jmeter_pb2_grpc


_ONE_DAY_IN_SECONDS = 60 * 60 * 24
GRPC_PORT = '[::]:50054'


class Controller(jmeter_pb2_grpc.ControllerServicer):

    def __init__(self, init_jmeter):
        logging.basicConfig(filename='jmeter_server.log',
                            level=logging.DEBUG)
        self.jmeter = 0
        if init_jmeter == 'init':
            print('init test')

    def GenTest(self, r, context):
        try:
            out_file = 'tests/test.jmx'
            template_file = 'tests/jmx.template'
            unames = pickle.loads(r.url_names)
            umethods = pickle.loads(r.url_methods)
            ulist = []
            for url in pickle.loads(r.url_list):
                u = urlparse(url)
                d = {}
                d['domain'] = u.hostname
                if u.port:
                    d['port'] = u.port
                else:
                    d['port'] = 80
                if u.path == '':
                    d['path'] = '/'
                else:
                    d['path'] = u.path
                ulist.append(d)

            with open(template_file) as f:
                tmpl = Template(f.read())
            output = tmpl.render(
                num_threads=r.num_threads,
                url_names=unames,
                url_methods=umethods,
                ramp_time=r.ramp_time,
                loops=r.loops,
                url_list=ulist
            )
            with open(out_file, "wb") as fh:
                fh.write(output)
            msg = 'Generated test plan'
        except Exception as e:
            logging.debug(e)
            msg = "Failed to generate test plan"
        return jmeter_pb2.JmeterReply(message=msg)

    def StartTest(self, r, context):
        try:
            if r.num_slaves == '0':
                self.jmeter = subprocess.Popen(
                 ["jmeter", "-n", "-t", "tests/test.jmx", "-l",
                            "default.jtl"], shell=False)
            else:
                slave_arg = "-R" + r.slave_ips
                self.jmeter = subprocess.Popen(
                 ["jmeter", "-n", "-t", "tests/test.jmx", slave_arg, "-l",
                            "default.jtl"], shell=False)
            msg = "Started jmeter on pid: {}".format(self.jmeter.pid)
        except Exception as e:
            logging.debug(e)
            msg = e
        return jmeter_pb2.JmeterReply(message=msg)

    def GetResults(self, r, context):
        try:
            if r.r_file == 'log':
                r_file = 'jmeter.log'
            else:
                r_file = 'default.jtl'
            f = open(r_file, 'r')
            msg = "Retrieved all results\n" + f.read()
        except Exception as e:
            logging.debug(e)
            msg = "Failed to retrieve results"
        return jmeter_pb2.JmeterReply(message=msg)


def serve(init_jmeter):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    jmeter_pb2_grpc.add_ControllerServicer_to_server(
                    Controller(init_jmeter), server)
    server.add_insecure_port(GRPC_PORT)
    server.start()
    try:
        while True:
            time.sleep(_ONE_DAY_IN_SECONDS)
    except KeyboardInterrupt:
        server.stop(0)


if __name__ == '__main__':
    serve(sys.argv[1])
