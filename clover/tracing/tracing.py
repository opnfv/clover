# Copyright (c) Authors of Clover
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0

import requests
import time
import redis

TRACING_IP = "localhost"
TRACING_PORT = "30888"


class Tracing:

    def __init__(
      self, tracing_ip, tracing_port, redis_ip='localhost', use_redis=True):
        self.tracing_ip = tracing_ip
        self.tracing_port = tracing_port
        self.testid = '0'
        self.test_start_time = 0
        self.use_redis = use_redis
        if use_redis:
            try:
                self.r = redis.StrictRedis(host=redis_ip, port=6379, db=0)
            except Exception:
                print("Failed to connect to redis")

    def setRedisSet(self, rkey, rvalue):
        if self.use_redis:
            self.r.sadd(rkey, rvalue)

    def setRedisList(self, rkey, rvalue):
        if self.use_redis:
            self.r.lpush(rkey, rvalue)

    def setRedisHash(self, rkey, rvalue):
        if self.use_redis:
            self.r.hmset(rkey, rvalue)

    def getRedisTestid(self, index):
        testid = self.r.lrange("testids", index, index)
        return testid[0]

    def getRedisTraceids(self, testid):
        rkey = "traceids:" + str(testid)
        traceids = self.r.smembers(rkey)
        return traceids

    def getRedisSpanids(self, traceid):
        rkey = "spanids:" + str(traceid)
        spanids = self.r.smembers(rkey)
        return spanids

    def getRedisSpan(self, spanid, traceid):
        rkey = "spans:" + str(traceid) + ':' + str(spanid)
        span = self.r.hgetall(rkey)
        return span

    def getRedisSpanValue(self, spanid, traceid, span_key):
        rkey = "spans:" + str(traceid) + ':' + str(spanid)
        span_value = self.r.hget(rkey, span_key)
        return span_value

    def getRedisTags(self, spanid, traceid):
        rkey = "tags:" + str(spanid) + ':' + str(traceid)
        tags = self.r.hgetall(rkey)
        return tags

    def getRedisTagsValue(self, spanid, traceid, tag_key):
        rkey = "tags:" + str(spanid) + ':' + str(traceid)
        tag_value = self.r.hget(rkey, tag_key)
        return tag_value

    def getRedisTestAll(self, testid):
        traceids = self.getRedisTraceids(testid)
        for trace in traceids:
            spanids = self.getRedisSpanids(trace)
            for span in spanids:
                # print(self.getRedisSpan(span, trace))
                print(self.getRedisSpanValue(span, trace, 'duration'))
                # print(self.getRedisTags(span, trace))
                print(self.getRedisTagsValue(span, trace, 'node_id'))

    def setTest(self, testid):
        self.testid = testid
        self.setRedisList("testids", testid)
        self.test_start_time = int(time.time())

    def getServices(self):
        req_url = 'http://' + self.tracing_ip + ':' + self.tracing_port + \
                                                        '/api/services'
        try:
            response = requests.get(req_url)
            if response.status_code != 200:
                print("ERROR: Cannot connect to tracing: {}".format(
                                        response.status_code))
                return False
        except Exception as e:
            print("ERROR: Cannot connect to tracing")
            print(e)
            return False

        data = response.json()
        services = data['data']
        return services

    def getTraces(self, service, time_back=3600, limit='1000'):
        ref_time = int(time.time())
        pad_time = '757000'
        end_time = 'end=' + str(ref_time) + pad_time + '&'
        if time_back == 0:
            delta = self.test_start_time
        else:
            delta = ref_time - time_back
        start_time = 'start=' + str(delta) + pad_time
        limit = 'limit=' + limit + '&'
        loopback = 'loopback=1h&'
        max_dur = 'maxDuration&'
        min_dur = 'minDuration&'
        service = 'service=' + service + '&'
        url_prefix = 'http://' + self.tracing_ip + ':' + self.tracing_port + \
            '/api/traces?'
        req_url = url_prefix + end_time + limit + loopback + max_dur + \
            min_dur + service + start_time

        try:
            response = requests.get(req_url)
            if response.status_code != 200:
                print("ERROR: Cannot connect to tracing: {}".format(
                                        response.status_code))
                return False
        except Exception as e:
            print("ERROR: Cannot connect to tracing")
            print(e)
            return False

        traces = response.json()
        return traces

    def numTraces(self, trace):
        num_traces = len(trace['data'])
        return str(num_traces)

    def outProcesses(self, trace):
        processes = []
        if trace['data']:
            first_trace = trace['data'][0]
            for process in first_trace['processes']:
                processes.append(process)
            print(processes)
        return processes

    def outTraces(self, trace):
        for traces in trace['data']:
            print("TraceID: {}".format(traces['traceID']))
            self.setRedisSet(
              "traceids:{}".format(str(self.testid)), traces['traceID'])
            for spans in traces['spans']:
                    print("SpanID: {}".format(spans['spanID']))
                    self.setRedisSet(
                       "spanids:{}".format(traces['traceID']), spans['spanID'])
                    print("Duration: {} usec".format(spans['duration']))
                    span = {}
                    span['spanID'] = spans['spanID']
                    span['duration'] = spans['duration']
                    span['startTime'] = spans['startTime']
                    span['operationName'] = spans['operationName']
                    # print("Tags:\n {} \n".format(spans['tags']))
                    self.setRedisHash(
                        "spans:{}:{}".format(
                           traces['traceID'], spans['spanID']), span)
                    tag = {}
                    for tags in spans['tags']:
                        print("Tag key: {}, value: {}".format(
                                tags['key'], tags['value']))
                        tag[tags['key']] = tags['value']
                    self.setRedisHash("tags:{}:{}".format(
                                spans['spanID'], traces['traceID']), tag)

    def monitorTraces(self, sample_interval, service='istio-ingress'):
        loop = True
        while loop:
            try:
                t = self.getTraces(service, 10)
                num_traces = self.numTraces(t)
                print("Number of traces: " + num_traces)
                self.outTraces(t)
                time.sleep(sample_interval)
            except KeyboardInterrupt:
                print("Test Start: {}".format(self.test_start_time))
                loop = False

    def main(self):
        self.monitorTraces(1)


if __name__ == '__main__':
    Tracing(TRACING_IP, TRACING_PORT).main()
