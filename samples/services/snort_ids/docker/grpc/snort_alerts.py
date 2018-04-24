# Copyright (c) Authors of Clover
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0

import redis
import logging
import grpc
import nginx_pb2
import nginx_pb2_grpc
from idstools import unified2


HOST_IP = 'redis'
# PROXY_GRPC = 'proxy-access-control:50054'

logging.basicConfig(filename='alert.log', level=logging.DEBUG)

connect = False
while not connect:
    try:
        r = redis.StrictRedis(host=HOST_IP, port=6379, db=0)
        r.delete('snort_events')
        connect = True
    except Exception as e:
        logging.debug(e)
        connect = False

reader = unified2.SpoolRecordReader("/var/log/snort",
                                    "", follow=True)


def sendGrpcAlert(event_id, redis_key):
    try:
        channel = grpc.insecure_channel('proxy-access-control:50054')
        stub = nginx_pb2_grpc.ControllerStub(channel)
        stub.ProcessAlerts(nginx_pb2.AlertMessage(
            event_id=event_id, redis_key=redis_key))
    except Exception as e:
        logging.debug(e)


for record in reader:
    try:
        if isinstance(record, unified2.Event):
            event = record
        elif isinstance(record, unified2.Packet):
            packet = record
        # elif isinstance(record, unified2.ExtraData):
            # print("Extra-Data:")
        snort_event = "snort_event:" + str(record['event-id'])
        r.sadd('snort_events', str(record['event-id']))
        event.update(packet)
        r.hmset(snort_event, event)
        sendGrpcAlert(str(record['event-id']), 'snort_events')
    except Exception as e:
        logging.debug(e)
