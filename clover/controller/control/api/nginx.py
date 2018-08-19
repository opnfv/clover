# Copyright (c) Authors of Clover
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0

from flask import Blueprint, request, Response
import grpc
import nginx_pb2
import nginx_pb2_grpc
import pickle
import logging

nginx = Blueprint('nginx', __name__)


@nginx.route("/nginx/slb", methods=['GET', 'POST'])
def slblist():
    grpc_port = '50054'
    try:
        p = request.json
        try:
            slb_name = p['slb_name']
            nginx_grpc = slb_name + ':' + grpc_port
            channel = grpc.insecure_channel(nginx_grpc)
            stub = nginx_pb2_grpc.ControllerStub(channel)

            s_list = []
            for s in p['slb_list']:
                s_list.append(s['url'])
            slb_list = pickle.dumps(s_list)
            response = stub.ModifyLB(nginx_pb2.ConfigLB(
                server_port=p['server_port'], server_name=p['server_name'],
                slb_list=slb_list,
                slb_group=p['slb_group'], lb_path=p['lb_path']))
        except (KeyError, ValueError) as e:
            logging.debug(e)
            return Response('Invalid value in test plan json/yaml', status=400)
    except Exception as e:
        logging.debug(e)
        if e.__class__.__name__ == "_Rendezvous":
            return Response("Error connecting to LB via gRPC", status=400)
        else:
            return Response("Error modifying LB server list", status=400)
    return response.message


@nginx.route("/nginx/test")
def test():
    return "<h1 style='color:blue'>Nginx API Test Response</h1>"
