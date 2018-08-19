# Copyright (c) Authors of Clover
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0

from flask import Blueprint, request, Response
import grpc
import jmeter_pb2
import jmeter_pb2_grpc
import pickle
import logging


jmeter = Blueprint('jmeter', __name__)

grpc_port = '50054'
pod_name = 'clover-jmeter-master'
jmeter_grpc = pod_name + ':' + grpc_port
channel = grpc.insecure_channel(jmeter_grpc)
stub = jmeter_pb2_grpc.ControllerStub(channel)


@jmeter.route("/jmeter/gen", methods=['GET', 'POST'])
def gentest():
    try:
        p = request.json
        u_list = []
        u_names = []
        u_methods = []
        try:
            for u in p['url_list']:
                u_list.append(u['url'])
                u_names.append(u['name'])
                u_methods.append(u['method'])
            url_list = pickle.dumps(u_list)
            url_names = pickle.dumps(u_names)
            url_methods = pickle.dumps(u_methods)
            num_threads = p['load_spec']['num_threads']
            ramp_time = p['load_spec']['ramp_time']
            loops = p['load_spec']['loops']
        except (KeyError, ValueError) as e:
            logging.debug(e)
            return Response('Invalid value in test plan json/yaml', status=400)
        response = stub.GenTest(jmeter_pb2.ConfigJmeter(
            url_list=url_list, url_names=url_names, url_methods=url_methods,
            num_threads=str(num_threads), ramp_time=str(ramp_time),
            loops=str(loops)))
    except Exception as e:
        logging.debug(e)
        if e.__class__.__name__ == "_Rendezvous":
            return Response("Error connecting to jmeter via gRPC", status=400)
        else:
            return Response("Error generating test plan", status=400)
    return response.message


@jmeter.route("/jmeter/start", methods=['GET', 'POST'])
def start():
    try:
        p = request.json
        if not p:
            slave_list = ''
            num_slaves = '0'
        else:
            slave_list = p['slave_list']
            num_slaves = p['num_slaves']
        response = stub.StartTest(jmeter_pb2.TestParams(
             num_slaves=num_slaves, test_plan='test.jmx',
             slave_ips=slave_list))
    except Exception as e:
        logging.debug(e)
        if e.__class__.__name__ == "_Rendezvous":
            return Response("Error connecting to jmeter via gRPC", status=400)
        else:
            return Response("Error starting jmeter test", status=400)
    return response.message


@jmeter.route("/jmeter/results/<r_type>", methods=['GET'])
def results(r_type):
    try:
        if not r_type:
            r_file = 'results'
        else:
            r_file = r_type
        response = stub.GetResults(jmeter_pb2.JResults(
            r_format='csv', r_file=r_file))
    except Exception as e:
        logging.debug(e)
        if e.__class__.__name__ == "_Rendezvous":
            return Response("Error connecting to jmeter via gRPC", status=400)
        else:
            return Response("Error returning results", status=400)
    return response.message


@jmeter.route("/jmeter/test")
def test():
    return "<h1 style='color:blue'>Jmeter API Test Response</h1>"
