# Copyright (c) Authors of Clover
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0

from flask import Blueprint, request, Response
import grpc
import snort_pb2
import snort_pb2_grpc
import logging
import redis

snort = Blueprint('snort', __name__)

grpc_port = '50052'
pod_name = 'snort-ids.default'
snort_grpc = pod_name + ':' + grpc_port
channel = grpc.insecure_channel(snort_grpc)
stub = snort_pb2_grpc.ControllerStub(channel)

HOST_IP = 'redis.default'


@snort.route("/snort/addrule", methods=['GET', 'POST'])
def addrule():
    try:
        try:
            p = request.json
            if p['content'] != "":
                response = stub.AddRules(snort_pb2.AddRule(
                    protocol=p['protocol'], dest_port=p['dest_port'],
                    dest_ip=p['dest_ip'], src_port=p['src_port'],
                    src_ip=p['src_ip'], msg=p['msg'], sid=p['sid'],
                    rev=p['rev'], content=p['content']))
            else:
                response = stub.AddRules(snort_pb2.AddRule(
                    protocol=p['protocol'], dest_port=p['dest_port'],
                    dest_ip=p['dest_ip'], src_port=p['src_port'],
                    src_ip=p['src_ip'], msg=p['msg'], sid=p['sid'],
                    rev=p['rev']))
        except (KeyError, ValueError) as e:
            logging.debug(e)
            return Response('Invalid value in IDS rule json/yaml', status=400)
    except Exception as e:
        logging.debug(e)
        if e.__class__.__name__ == "_Rendezvous":
            return Response("Error connecting to IDS via gRPC", status=400)
        else:
            return Response("Error adding IDS rule", status=400)
    return response.message


@snort.route("/snort/start")
def start():
    try:
        response = stub.StartSnort(snort_pb2.ControlSnort(pid='0'))
    except Exception as e:
        logging.debug(e)
        if e.__class__.__name__ == "_Rendezvous":
            return Response("Error connecting to jmeter via gRPC", status=400)
        else:
            return Response("Error starting IDS", status=400)
    return response.message


@snort.route("/snort/stop")
def stop():
    try:
        response = stub.StopSnort(snort_pb2.ControlSnort(pid='0'))
    except Exception as e:
        logging.debug(e)
        if e.__class__.__name__ == "_Rendezvous":
            return Response("Error connecting to jmeter via gRPC", status=400)
        else:
            return Response("Error stopping IDS", status=400)
    return response.message


@snort.route("/snort/get_events", methods=['GET'])
def get_events():
    try:
        p = request.json
        r = redis.StrictRedis(host=HOST_IP, port=6379, db=0)
        event_data = r.hget(p['event_key'], p['field'])
        response = event_data
    except Exception as e:
        logging.debug(e)
        if e.__class__.__name__ == "_Rendezvous":
            return Response("Error connecting to jmeter via gRPC", status=400)
        else:
            return Response("Error returning IDS event", status=400)
    return response


@snort.route("/snort/test")
def test():
    return "<h1 style='color:blue'>Snort API Test Response</h1>"
