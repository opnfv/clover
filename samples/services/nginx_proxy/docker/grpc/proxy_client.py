# Copyright (c) Authors of Clover
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0

from __future__ import print_function

import grpc

import proxy_pb2
import proxy_pb2_grpc


PROXY_GRPC = '10.244.0.111:50054'
# PROXY_GRPC = 'localhost:50054'


def run():
    channel = grpc.insecure_channel(PROXY_GRPC)
    stub = proxy_pb2_grpc.ControllerStub(channel)

    response = stub.ModifyConfig(proxy_pb2.AddConfig(
            server_port='9180', server_name='http-proxy',
            location_path='/', proxy_path='http://clover-server:9180',
            mirror_path='http://snort-ids:80'))
    print(response.message)


if __name__ == '__main__':
    run()
