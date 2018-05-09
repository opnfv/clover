# Copyright (c) Authors of Clover
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0

from __future__ import print_function
# from kubernetes import client, config

import grpc
import argparse
import pickle

import collector_pb2
import collector_pb2_grpc

# This is a basic client script to test server GRPC messaging
# TODO improve interface overall


def run(args, grpc_port='50054'):
    pod_ip = 'localhost'
    collector_grpc = pod_ip + ':' + grpc_port
    channel = grpc.insecure_channel(collector_grpc)
    stub = collector_pb2_grpc.ControllerStub(channel)

    if args['cmd'] == 'init':
        return init_visibility(stub)
    elif args['cmd'] == 'start':
        return start_collector(stub)
    elif args['cmd'] == 'stop':
        return stop_collector(stub)
    else:
        return "Invalid command: {}".format(args['cmd'])


def init_visibility(stub):
    try:
        cassandra_hosts = pickle.dumps(['172.17.0.3'])
        response = stub.InitVisibility(collector_pb2.ConfigCassandra(
            cassandra_hosts=cassandra_hosts, cassandra_port=9042))
    except Exception as e:
        return e
    return response.message


def start_collector(stub):
    try:
        cassandra_hosts = pickle.dumps(['172.17.0.3'])
        response = stub.StartCollector(collector_pb2.ConfigCollector(
            t_port='30869', t_host='localhost',
            m_port='9090', m_host='10.244.0.198',
            c_port='9042', c_hosts=cassandra_hosts,
            sinterval='5'
            ))
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
