# Copyright (c) Authors of Clover
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0


from concurrent import futures
from clover.collector.db.cassops import CassandraOps
import time
import sys
import grpc
import subprocess
import pickle
import logging
import collector_pb2
import collector_pb2_grpc


_ONE_DAY_IN_SECONDS = 60 * 60 * 24
GRPC_PORT = '[::]:50054'


class Controller(collector_pb2_grpc.ControllerServicer):

    def __init__(self, init_visibility):
        logging.basicConfig(filename='collector_server.log',
                            level=logging.DEBUG)
        self.collector = 0
        if init_visibility == 'set_schemas':
            cassandra_hosts = pickle.dumps(['cassandra.clover-system'])
            self.InitVisibility(collector_pb2.ConfigCassandra(
               cassandra_port=9042, cassandra_hosts=cassandra_hosts), "")

    def StopCollector(self, r, context):
        try:
            subprocess.Popen.kill(self.collector)
            msg = "Stopped collector on pid: {}".format(self.collector.pid)
        except Exception as e:
            logging.debug(e)
            msg = "Failed to stop collector"
        return collector_pb2.CollectorReply(message=msg)

    def StartCollector(self, r, context):
        try:
            self.collector = subprocess.Popen(
              ["python", "process/collect.py",
               "-sinterval={}".format(r.sinterval),
               "-c_port={}".format(r.c_port),
               "-t_port={}".format(r.t_port), "-t_host={}".format(r.t_host),
               "-m_port={}".format(r.m_port), "-m_host={}".format(r.m_host),
               "-c_hosts={}".format(pickle.loads(r.c_hosts)), "&"],
              shell=False)
            msg = "Started collector on pid: {}".format(self.collector.pid)
        except Exception as e:
            logging.debug(e)
            msg = e
        return collector_pb2.CollectorReply(message=msg)

    def InitVisibility(self, r, context):
        try:
            cass = CassandraOps(pickle.loads(r.cassandra_hosts),
                                r.cassandra_port)
            cass.init_visibility()
            msg = "Added visibility schemas in cassandra"
        except Exception as e:
            logging.debug(e)
            msg = "Failed to initialize cassandra"
        return collector_pb2.CollectorReply(message=msg)

    def TruncateVisibility(self, r, context):
        try:
            cass = CassandraOps(pickle.loads(r.cassandra_hosts),
                                r.cassandra_port)
            cass.truncate(pickle.loads(r.schemas))
            msg = "Truncated visibility tables"
        except Exception as e:
            logging.debug(e)
            msg = "Failed to truncate visibility"
        return collector_pb2.CollectorReply(message=msg)


def serve(init_visibility):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    collector_pb2_grpc.add_ControllerServicer_to_server(
                    Controller(init_visibility), server)
    server.add_insecure_port(GRPC_PORT)
    server.start()
    try:
        while True:
            time.sleep(_ONE_DAY_IN_SECONDS)
    except KeyboardInterrupt:
        server.stop(0)


if __name__ == '__main__':
    serve(sys.argv[1])
