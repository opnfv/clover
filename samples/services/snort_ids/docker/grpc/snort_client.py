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

import snort_pb2
import snort_pb2_grpc


def run(args, grpc_port='50052'):
    # get pod ip for grpc
    pod_ip = get_podip(args['service_name'])
    if pod_ip == '':
        return "Can not find service: {}".format(args['service_name'])
    snort_grpc = pod_ip + ':' + grpc_port
    # snort_grpc = 'localhost:50052'
    channel = grpc.insecure_channel(snort_grpc)
    stub = snort_pb2_grpc.ControllerStub(channel)

    # execute command in service
    if args['cmd'] == 'addtcp':
        return add_tcprule(stub)
    elif args['cmd'] == 'addicmp':
        return add_icmprule(stub)
    elif args['cmd'] == 'addscan':
        return add_scanrule(stub)
    elif args['cmd'] == 'start':
        return start_snort(stub)
    elif args['cmd'] == 'stop':
        return stop_snort(stub)
    else:
        return "Invalid command: {}".format(args['cmd'])


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


def add_tcprule(stub):
    try:
        response = stub.AddRules(snort_pb2.AddRule(
             protocol='tcp', dest_port='any', dest_ip='$HOME_NET',
             src_port='any', src_ip='any', msg='tcp test', sid='10000002',
             rev='001'))
        print(stop_snort(stub))
        print(start_snort(stub))
    except Exception as e:
        return e
    return response.message


def add_icmprule(stub):
    try:
        response = stub.AddRules(snort_pb2.AddRule(
            protocol='icmp', dest_port='any', dest_ip='$HOME_NET',
            src_port='any', src_ip='any', msg='icmp test', sid='10000001',
            rev='001'))
        print(stop_snort(stub))
        print(start_snort(stub))
    except Exception as e:
        return e
    return response.message


def add_scanrule(stub):
    try:
        response = stub.AddRules(snort_pb2.AddRule(
            protocol='tcp', dest_port='any', dest_ip='$HOME_NET',
            src_port='any', src_ip='any',
            msg='MALWARE-CNC User-Agent ASafaWeb Scan', sid='10000003',
            rev='001', content='"asafaweb.com"'))
        print(stop_snort(stub))
        print(start_snort(stub))
    except Exception as e:
        return e
    return response.message


def start_snort(stub):
    try:
        response = stub.StartSnort(snort_pb2.ControlSnort(pid='0'))
    except Exception as e:
        return e
    return response.message


def stop_snort(stub):
    try:
        response = stub.StopSnort(snort_pb2.ControlSnort(pid='0'))
    except Exception as e:
        return e
    return response.message


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
            '--service_name', required=True,
            help='Snort service/pod name to reconfigure')
    parser.add_argument(
            '--cmd', required=True,
            help='Command to execute in snort service')
    args = parser.parse_args()
    print(run(vars(args)))
