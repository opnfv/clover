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

import collector_pb2
import collector_pb2_grpc

# This is a basic client script to test server GRPC messaging
# TODO improve interface overall


def run(args, grpc_port='50054'):
    pod_ip = get_podip('clover-collector')
    if pod_ip == '':
        return "Can not find service: {}".format(args['service_name'])
    collector_grpc = pod_ip + ':' + grpc_port
    channel = grpc.insecure_channel(collector_grpc)
    stub = collector_pb2_grpc.ControllerStub(channel)

    if args['cmd'] == 'init':
        return init_visibility(stub)
    elif args['cmd'] == 'start':
        return start_collector(stub)
    elif args['cmd'] == 'stop':
        return stop_collector(stub)
    elif args['cmd'] == 'clean':
        return clean_visibility(stub)
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


def init_visibility(stub):
    try:
        cassandra_hosts = pickle.dumps(['cassandra.default'])
        response = stub.InitVisibility(collector_pb2.ConfigCassandra(
            cassandra_hosts=cassandra_hosts, cassandra_port=9042))
    except Exception as e:
        return e
    return response.message


def clean_visibility(stub):
    try:
        cassandra_hosts = pickle.dumps(['cassandra.default'])
        schemas = pickle.dumps(['spans', 'traces', 'metrics'])
        response = stub.TruncateVisibility(collector_pb2.Schemas(
            schemas=schemas, cassandra_hosts=cassandra_hosts,
            cassandra_port=9042))
    except Exception as e:
        return e
    return response.message


def start_collector(stub):
    try:
        cassandra_hosts = pickle.dumps(['cassandra.default'])
        response = stub.StartCollector(collector_pb2.ConfigCollector(
            t_port='16686', t_host='jaeger-deployment.istio-system',
            m_port='9090', m_host='prometheus.istio-system',
            c_port='9042', c_hosts=cassandra_hosts,
            sinterval='5'))
    except Exception as e:
        return e
    return response.message


def stop_collector(stub):
    try:
        response = stub.StopCollector(collector_pb2.ConfigCollector())
    except Exception as e:
        return e
    return response.message


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
            '--cmd', required=True,
            help='Command to execute in collector')
    args = parser.parse_args()
    print(run(vars(args)))
