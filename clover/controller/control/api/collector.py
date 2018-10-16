# Copyright (c) Authors of Clover
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0

from flask import Blueprint, request, Response
import grpc
import pickle
import collector_pb2
import collector_pb2_grpc
import redis
import logging


collector = Blueprint('collector', __name__)

grpc_port = '50054'
pod_name = 'clover-collector.clover-system'
collector_grpc = pod_name + ':' + grpc_port
channel = grpc.insecure_channel(collector_grpc)
stub = collector_pb2_grpc.ControllerStub(channel)
CASSANDRA_HOSTS = pickle.dumps(['cassandra.clover-system'])

HOST_IP = 'redis.default'


@collector.route("/collector/init")
def init():
    try:
        response = stub.InitVisibility(collector_pb2.ConfigCassandra(
            cassandra_hosts=CASSANDRA_HOSTS, cassandra_port=9042))
    except Exception as e:
        logging.debug(e)
        if e.__class__.__name__ == "_Rendezvous":
            return Response("Error connecting via gRPC", status=400)
        else:
            return Response("Error initializing visibility", status=400)
    return response.message


@collector.route("/collector/truncate")
def truncate():
    try:
        schemas = pickle.dumps(['spans', 'traces', 'metrics'])
        response = stub.TruncateVisibility(collector_pb2.Schemas(
            schemas=schemas, cassandra_hosts=CASSANDRA_HOSTS,
            cassandra_port=9042))
    except Exception as e:
        logging.debug(e)
        if e.__class__.__name__ == "_Rendezvous":
            return Response("Error connecting via gRPC", status=400)
        else:
            return Response("Error truncating visibility", status=400)
    return response.message


@collector.route("/collector/start", methods=['GET', 'POST'])
def start():
    try:
        p = request.json
        if not p:
            sample_interval = '5'
            t_host = 'tracing.istio-system'
            t_port = '16686'
            m_host = 'prometheus.istio-system'
            m_port = '9090'
        else:
            try:
                sample_interval = p['sample_interval']
                t_host = p['t_host']
                t_port = p['t_port']
                m_host = p['m_host']
                m_port = p['m_port']
            except (KeyError, ValueError) as e:
                logging.debug(e)
                return Response("Invalid value in json/yaml", status=400)
        response = stub.StartCollector(collector_pb2.ConfigCollector(
            t_port=t_port, t_host=t_host,
            m_port=m_port, m_host=m_host,
            c_port='9042', c_hosts=CASSANDRA_HOSTS,
            sinterval=sample_interval))
    except Exception as e:
        logging.debug(e)
        if e.__class__.__name__ == "_Rendezvous":
            return Response("Error connecting via gRPC", status=400)
        else:
            return Response("Error starting visibility", status=400)
    return response.message


@collector.route("/collector/stop")
def stop():
    try:
        response = stub.StopCollector(collector_pb2.ConfigCollector())
    except Exception as e:
        logging.debug(e)
        if e.__class__.__name__ == "_Rendezvous":
            return Response("Error connecting via gRPC", status=400)
        else:
            return Response("Error stopping visibility", status=400)
    return response.message


@collector.route("/collector/set", methods=['GET', 'POST'])
def set_collector():
    try:
        p = request.json
        r = redis.StrictRedis(host=HOST_IP, port=6379, db=0)
        del_keys = ['visibility_services', 'metric_prefixes',
                    'metric_suffixes', 'custom_metrics']
        for dk in del_keys:
            r.delete(dk)

        try:
            for service in p['services']:
                r.sadd('visibility_services', service['name'])
        except (KeyError, ValueError) as e:
            logging.debug(e)
            return Response(
                         "Specify at least one service to track", status=400)
        if p['metric_prefixes'] and p['metric_suffixes']:
            for prefix in p['metric_prefixes']:
                r.sadd('metric_prefixes', prefix['prefix'])
            for suffix in p['metric_suffixes']:
                r.sadd('metric_suffixes', suffix['suffix'])
        if p['custom_metrics']:
            for metric in p['custom_metrics']:
                r.sadd('custom_metrics', metric['metric'])

    except Exception as e:
        logging.debug(e)
        return Response("Error setting visibility config", status=400)
    return Response("Updated visibility config", status=200)


@collector.route("/collector/test")
def test():
    return "<h1 style='color:blue'>Collector API Test Response</h1>"
