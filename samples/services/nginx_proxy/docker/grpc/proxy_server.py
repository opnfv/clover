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
import logging
import proxy_pb2
import proxy_pb2_grpc

from jinja2 import Template

_ONE_DAY_IN_SECONDS = 60 * 60 * 24
GRPC_PORT = '[::]:50054'


class Controller(proxy_pb2_grpc.ControllerServicer):

    def __init__(self):
        self.x = 0
        logging.basicConfig(filename='proxy.log', level=logging.DEBUG)

    def ModifyConfig(self, r, context):
        try:
            # out_file = 'testfile'
            out_file = '/etc/nginx/nginx.conf'
            template_file = '/grpc/proxy.template'
            with open(template_file) as f:
                tmpl = Template(f.read())
            output = tmpl.render(
                server_port=r.server_port,
                server_name=r.server_name,
                location_path=r.location_path,
                proxy_path=r.proxy_path,
                mirror_path=r.mirror_path
            )
            with open(out_file, "wb") as fh:
                fh.write(output)
            subprocess.Popen(
                  ["service nginx restart"], shell=True)
            msg = "Modified proxy config"
        except Exception as e:
            logging.debug(e)
            msg = "Failed to modify proxy config"
        return proxy_pb2.ProxyReply(message=msg)

    def ProcessAlerts(self, request, context):
        try:
            msg = "Processed alert"
        except Exception as e:
            logging.debug(e)
            msg = "Failed to process alert"
        return proxy_pb2.ProxyReply(message=msg)


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    proxy_pb2_grpc.add_ControllerServicer_to_server(Controller(), server)
    server.add_insecure_port(GRPC_PORT)
    server.start()
    try:
        while True:
            time.sleep(_ONE_DAY_IN_SECONDS)
    except KeyboardInterrupt:
        server.stop(0)


if __name__ == '__main__':
    serve()
