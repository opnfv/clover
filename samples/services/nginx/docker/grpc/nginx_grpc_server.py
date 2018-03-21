# Copyright (c) Authors of Clover
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0


from concurrent import futures
import time
import sys
import grpc
import subprocess
import pickle
import logging
import nginx_pb2
import nginx_pb2_grpc

from jinja2 import Template

_ONE_DAY_IN_SECONDS = 60 * 60 * 24
GRPC_PORT = '[::]:50054'


class Controller(nginx_pb2_grpc.ControllerServicer):

    def __init__(self, service_type):
        logging.basicConfig(filename='nginx.log', level=logging.DEBUG)
        self.service_type = service_type
        self.out_file = '/etc/nginx/nginx.conf'
        # self.out_file = 'testfile'
        if service_type == "proxy":
            # self.template_file = 'templates/proxy.template'
            self.template_file = '/grpc/templates/proxy.template'
            self.ModifyProxy(nginx_pb2.ConfigProxy(
                server_port='9180', server_name='http-proxy',
                location_path='/', proxy_path='http://clover-server:9180',
                mirror_path='http://snort-ids:80'), "")
        if service_type == "server":
            # self.template_file = 'templates/server.template'
            self.template_file = '/grpc/templates/server.template'
            self.ModifyServer(nginx_pb2.ConfigServer(
                server_port='9180', server_name='clover-server',
                site_root='/var/www/html',
                site_index='index.nginx-debian.html'), "")
        if service_type == "lb":
            # self.template_file = 'templates/lb.template'
            self.template_file = '/grpc/templates/lb.template'
            slb_list = pickle.dumps(
                    ['clover-server1', 'clover-server2', 'clover-server3'])
            self.ModifyLB(nginx_pb2.ConfigLB(
                server_port='9188', server_name='clover-lb',
                slb_list=slb_list,
                slb_group='cloverlb', lb_path='/'), "")

    def ModifyProxy(self, r, context):
        try:
            with open(self.template_file) as f:
                tmpl = Template(f.read())
            output = tmpl.render(
                server_port=r.server_port,
                server_name=r.server_name,
                location_path=r.location_path,
                proxy_path=r.proxy_path,
                mirror_path=r.mirror_path
            )
            with open(self.out_file, "wb") as fh:
                fh.write(output)
            msg = "Modified nginx config"
            self.RestartNginx()
        except Exception as e:
            logging.debug(e)
            msg = "Failed to modify nginx config"
        return nginx_pb2.NginxReply(message=msg)

    def ModifyServer(self, r, context):
        try:
            with open(self.template_file) as f:
                tmpl = Template(f.read())
            output = tmpl.render(
                server_port=r.server_port,
                server_name=r.server_name,
                site_root=r.site_root,
                site_index=r.site_index
            )
            with open(self.out_file, "wb") as fh:
                fh.write(output)
            msg = "Modified nginx config"
            self.RestartNginx()
        except Exception as e:
            logging.debug(e)
            msg = "Failed to modify nginx config"
        return nginx_pb2.NginxReply(message=msg)

    def ModifyLB(self, r, context):
        try:
            with open(self.template_file) as f:
                tmpl = Template(f.read())
            output = tmpl.render(
                server_port=r.server_port,
                server_name=r.server_name,
                slb_list=pickle.loads(r.slb_list),
                slb_group=r.slb_group,
                lb_path=r.lb_path
            )
            with open(self.out_file, "wb") as fh:
                fh.write(output)
            msg = "Modified nginx config"
            self.RestartNginx()
        except Exception as e:
            logging.debug(e)
            msg = "Failed to modify nginx config"
        return nginx_pb2.NginxReply(message=msg)

    def RestartNginx(self):
        subprocess.Popen(
                  ["service nginx restart"], shell=True)

    def ProcessAlerts(self, request, context):
        try:
            msg = "Processed alert"
        except Exception as e:
            logging.debug(e)
            msg = "Failed to process alert"
        return nginx_pb2.NginxReply(message=msg)


def serve(service_type):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    nginx_pb2_grpc.add_ControllerServicer_to_server(
                    Controller(service_type), server)
    server.add_insecure_port(GRPC_PORT)
    server.start()
    try:
        while True:
            time.sleep(_ONE_DAY_IN_SECONDS)
    except KeyboardInterrupt:
        server.stop(0)


if __name__ == '__main__':
    serve(sys.argv[1])
