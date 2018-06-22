# Copyright (c) Authors of Clover
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0


from concurrent import futures
import time
import os
import sys
import grpc
import subprocess
import psutil
import shutil
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
        self.nginx = 0
        if service_type == "proxy":
            self.template_file = '/grpc/templates/proxy.template'
            self.ModifyProxy(nginx_pb2.ConfigProxy(
                server_port='9180', server_name='proxy-access-control',
                location_path='/', proxy_path='http://http-lb:9180',
                mirror_path='http://snort-ids:80'), "")
        if service_type == "server":
            self.template_file = '/grpc/templates/server.template'
            loc = []
            val = {}
            val['uri_match'] = "/test"
            val['directive'] = "try_files $uri @default1"
            val['path'] = "/test"
            loc.append(val)
            locations = pickle.dumps(loc)
            files = pickle.dumps([])
            self.ModifyServer(nginx_pb2.ConfigServer(
                server_port='9180', server_name='clover-server',
                site_root='/var/www/html',
                upload_path_config='/upload',
                upload_path_test='/upload_test',
                locations=locations,
                files=files,
                site_index='index.html'), "")
        if service_type == "lb":
            self.template_file = '/grpc/templates/lb.template'
            slb_list = pickle.dumps(
                    ['clover-server1:9180', 'clover-server2:9180',
                        'clover-server3:9180'])
            self.ModifyLB(nginx_pb2.ConfigLB(
                server_port='9180', server_name='http-lb',
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
            locations = pickle.loads(r.locations)
            # Generate nginx config
            with open(self.template_file) as f:
                tmpl = Template(f.read())
            output = tmpl.render(
                server_port=r.server_port,
                server_name=r.server_name,
                site_root=r.site_root,
                site_index=r.site_index,
                upload_path_config=r.upload_path_config,
                upload_path_test=r.upload_path_test,
                locations=locations
            )
            with open(self.out_file, "wb") as fh:
                fh.write(output)

            # Make dirs for locations
            for l in locations:
                self.MakeDirs(l['path'])

            # Generate upload form for config
            template_upload = '/grpc/templates/upload_form.template'
            out_file = r.site_root + '/' + r.site_index
            with open(template_upload) as f:
                tmpl = Template(f.read())
            output = tmpl.render(
                upload_path=r.upload_path_config
            )
            with open(out_file, "wb") as fh:
                fh.write(output)

            # Generate upload form for test
            template_upload = '/grpc/templates/upload_form.template'
            out_file = r.site_root + '/' + 'upload_test.html'
            with open(template_upload) as f:
                tmpl = Template(f.read())
            output = tmpl.render(
                upload_path=r.upload_path_test
            )
            with open(out_file, "wb") as fh:
                fh.write(output)

            msg = "Modified nginx config"
            self.RestartNginx('custom')

            # Move files that have been uploaded
            file_ops = pickle.loads(r.files)
            self.MoveServerFiles(file_ops)
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

    def DeleteServerFiles(self, upload_folder):
        for f in os.listdir(upload_folder):
            file_path = os.path.join(upload_folder, f)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            except Exception as e:
                logging.debug(e)

    def MoveServerFiles(self, file_ops):
        response = 1
        try:
            for fo in file_ops:
                try:
                    shutil.move(fo['src_file'], fo['dest_file'])
                except Exception as e:
                    logging.debug(e)
                    response = 0
        except Exception as e:
            logging.debug(e)
        return response

    def RestartNginx(self, package='default'):
        if package == 'custom':
            if self.nginx == 0:
                p = subprocess.Popen(["nginx"],
                                     stdout=subprocess.PIPE,
                                     shell=True,
                                     preexec_fn=os.setsid)
            else:
                for proc in psutil.process_iter():
                    if proc.name() == "nginx":
                        proc.kill()
                p = subprocess.Popen(["nginx"],
                                     stdout=subprocess.PIPE,
                                     shell=True,
                                     preexec_fn=os.setsid)
            self.nginx = p
        else:
            subprocess.Popen(
                      ["service nginx restart"], shell=True)

    def MakeDirs(self, path, prefix='/var/www/html/'):
        try:
            path = prefix + path.strip('/')
            os.makedirs(path)
        except Exception as e:
            logging.debug(e)

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
