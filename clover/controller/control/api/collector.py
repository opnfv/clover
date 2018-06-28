# Copyright (c) Authors of Clover
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0

from flask import Blueprint, request
import grpc
import pickle
import collector_pb2
import collector_pb2_grpc


collector = Blueprint('collector', __name__)

grpc_port = '50054'
pod_name = 'clover-collector'
collector_grpc = pod_name + ':' + grpc_port
channel = grpc.insecure_channel(collector_grpc)
stub = collector_pb2_grpc.ControllerStub(channel)
cassandra_hosts = pickle.dumps(['cassandra.default'])


@collector.route("/collector/init")
def init():
    try:
        response = stub.InitVisibility(collector_pb2.ConfigCassandra(
            cassandra_hosts=cassandra_hosts, cassandra_port=9042))
    except Exception as e:
        return e
    return response.message


@collector.route("/collector/truncate")
def truncate():
    try:
        schemas = pickle.dumps(['spans', 'traces', 'metrics'])
        response = stub.TruncateVisibility(collector_pb2.Schemas(
            schemas=schemas, cassandra_hosts=cassandra_hosts,
            cassandra_port=9042))
    except Exception as e:
        return e
    return response.message


@collector.route("/collector/start", methods=['GET', 'POST'])
def start():
    try:
        p = request.json
        if not p:
            sample_interval = '5'
        else:
            sample_interval = p['sample_interval']
        response = stub.StartCollector(collector_pb2.ConfigCollector(
            t_port='16686', t_host='jaeger-deployment.istio-system',
            m_port='9090', m_host='prometheus.istio-system',
            c_port='9042', c_hosts=cassandra_hosts,
            sinterval=sample_interval))
    except Exception as e:
        return e
    return response.message


@collector.route("/collector/stop")
def stop():
    try:
        response = stub.StopCollector(collector_pb2.ConfigCollector())
    except Exception as e:
        return e
    return response.message


@collector.route("/collector/test")
def test():
    return "<h1 style='color:blue'>Collector API Test Response</h1>"
