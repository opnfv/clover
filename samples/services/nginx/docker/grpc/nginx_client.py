# Copyright (c) Authors of Clover
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0

from __future__ import print_function

import grpc
import pickle

import nginx_pb2
import nginx_pb2_grpc


NGINX_GRPC = '10.244.0.120:50054'
# NGINX_GRPC = 'localhost:50054'


def run():
    channel = grpc.insecure_channel(NGINX_GRPC)
    stub = nginx_pb2_grpc.ControllerStub(channel)

    # response = stub.ModifyProxy(nginx_pb2.ConfigProxy(
    #         server_port='9180', server_name='http-proxy',
    #         location_path='/', proxy_path='http://clover-server:9180',
    #         mirror_path='http://snort-ids:80'))
    # print(response.message)

    # response = stub.ModifyServer(nginx_pb2.ConfigServer(
    #         server_port='9180', server_name='clover-server',
    #         site_root='/var/www/html', site_index='index.nginx-debian.html'))
    # print(response.message)

    slb_list = pickle.dumps(
                    ['clover-server1', 'clover-server2', 'clover-server3'])
    response = stub.ModifyLB(nginx_pb2.ConfigLB(
            server_port='9188', server_name='clover-lb',
            slb_list=slb_list,
            slb_group='cloverlb', lb_path='/'))
    print(response.message)


if __name__ == '__main__':
    run()
