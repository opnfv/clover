# Copyright (c) Authors of Clover
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0

from concurrent import futures
import time

import grpc
import subprocess
import os

import snort_pb2
import snort_pb2_grpc

_ONE_DAY_IN_SECONDS = 60 * 60 * 24
GRPC_PORT = '[::]:50052'


class Controller(snort_pb2_grpc.ControllerServicer):

    def __init__(self):
        self.snort = 0

    def AddRules(self, r, context):
        try:
            # file_local = 'testfile'
            file_local = '/etc/snort/rules/local.rules'
            f = open(file_local, 'a')
            rule = 'alert {} {} {} -> {} {} '.format(
                r.protocol, r.src_ip, r.src_port, r.dest_ip, r.dest_port) \
                + '(msg:"{}"; sid:{}; rev:{};)\n'.format(r.msg, r.sid, r.rev)
            f.write(rule)
            f.close
            msg = "Added to local rules"
        except Exception as e:
            msg = "Failed to add to local rules"
            print(e)
        return snort_pb2.SnortReply(message=msg)

    def StartSnort(self, request, context):
        try:
            if self.snort == 0:
                p = subprocess.Popen(
                  ["snort -i eth0 -u snort -g snort -c /etc/snort/snort.conf \
                                                -k none"], shell=True)
                self.snort = p
                msg = "Started Snort on pid: {}".format(p.pid)
            else:
                msg = "Snort already running"
        except Exception:
            self.snort = 0
            msg = "Failed to start Snort"
        return snort_pb2.SnortReply(message=msg)

    def StopSnort(self, request, context):
        subprocess.Popen.kill(self.snort)
        msg1 = "Stopped Snort on pid: {}".format(self.snort.pid)
        self.snort = 0
        logPath = '/var/log/snort'
        logList = os.listdir(logPath)
        for logName in logList:
            os.remove(logPath+"/"+logName)
        msg2 = "Cleared Snort logs"
        msg = msg1 + msg2
        return snort_pb2.SnortReply(message=msg)


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    snort_pb2_grpc.add_ControllerServicer_to_server(Controller(), server)
    server.add_insecure_port(GRPC_PORT)
    server.start()
    try:
        while True:
            time.sleep(_ONE_DAY_IN_SECONDS)
    except KeyboardInterrupt:
        server.stop(0)


if __name__ == '__main__':
    serve()
