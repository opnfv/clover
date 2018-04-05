# Copyright (c) Authors of Clover
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0

from __future__ import print_function
from kubernetes import client, config

import grpc
import argparse
import pickle

import nginx_pb2
import nginx_pb2_grpc


def run(args, grpc_port='50054'):
    # get pod ip for grpc
    pod_ip = get_podip(args['service_name'])
    if pod_ip == '':
        return "Cant find service: {}".format(args['service_name'])
    nginx_grpc = pod_ip + ':' + grpc_port
    channel = grpc.insecure_channel(nginx_grpc)
    stub = nginx_pb2_grpc.ControllerStub(channel)

    # modify config
    if args['service_type'] == 'lbv1':
        slb_list = pickle.dumps(
                    ['clover-server1:9180', 'clover-server2:9180'])
        modify_lb(stub, slb_list)
    if args['service_type'] == 'lbv2':
        slb_list = pickle.dumps(
                    ['clover-server4:9180', 'clover-server5:9180'])
        modify_lb(stub, slb_list)
    elif args['service_type'] == 'proxy':
        modify_proxy(stub)
    elif args['service_type'] == 'server':
        modify_server(stub)
    else:
        return "Invalid service type: {}".format(args['service_type'])
    return "Modification complete"


def get_podip(pod_name):
    ip = ''
    if pod_name != '':
        config.load_kube_config()
        v1 = client.CoreV1Api()
        ret = v1.list_pod_for_all_namespaces(watch=False)
        for i in ret.items:
            if i.metadata.name.lower().find(pod_name.lower()) != -1:
                print("Pod IP: {}".format(i.status.pod_ip))
                ip = i.status.pod_ip
                return str(ip)
    return str(ip)


def modify_proxy(stub):
    response = stub.ModifyProxy(nginx_pb2.ConfigProxy(
            server_port='9180', server_name='http-proxy',
            location_path='/', proxy_path='http://clover-server:9180',
            mirror_path='http://snort-ids:80'))
    print(response.message)


def modify_server(stub):
    response = stub.ModifyServer(nginx_pb2.ConfigServer(
            server_port='9180', server_name='clover-server',
            site_root='/var/www/html', site_index='index.nginx-debian.html'))
    print(response.message)


def modify_lb(stub, slb_list):
    response = stub.ModifyLB(nginx_pb2.ConfigLB(
            server_port='9180', server_name='http-lb',
            slb_list=slb_list,
            slb_group='cloverlb', lb_path='/'))
    print(response.message)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
            '--service_type', required=True,
            help='The service to reconfigure')
    parser.add_argument(
            '--service_name', required=True,
            help='The service to reconfigure')

    args = parser.parse_args()
    print(run(vars(args)))
