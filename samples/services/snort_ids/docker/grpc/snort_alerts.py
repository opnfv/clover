# Copyright (c) Authors of Clover
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0

import redis
import grpc
import proxy_pb2
import proxy_pb2_grpc
from idstools import unified2


HOST_IP = 'redis'
PROXY_GRPC = 'http-proxy:50054'

connect = False
while not connect:
    try:
        r = redis.StrictRedis(host=HOST_IP, port=6379, db=0)
        r.delete('snort_events')
        connect = True
    except Exception:
        connect = False

reader = unified2.SpoolRecordReader("/var/log/snort",
                                    "", follow=True)


def sendGrpcAlert(event_id, redis_key):
    try:
        channel = grpc.insecure_channel(PROXY_GRPC)
        stub = proxy_pb2_grpc.ControllerStub(channel)
        stub.ProcessAlerts(proxy_pb2.AlertMessage(
            event_id=event_id, redis_key=redis_key))
    except Exception:
        print "Cannot send GRPC"


for record in reader:
    try:
        if isinstance(record, unified2.Event):
            print("Event:")
            snort_event = "snort_event:" + str(record['event-id'])
            r.sadd('snort_events', str(record['event-id']))
            r.hmset(snort_event, record)
            sendGrpcAlert(str(record['event-id']), 'snort_events')
        elif isinstance(record, unified2.Packet):
            print("Packet:")
        elif isinstance(record, unified2.ExtraData):
            print("Extra-Data:")
        print(record)
    except Exception as e:
        print(e)
