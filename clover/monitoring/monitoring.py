# Copyright (c) Authors of Clover
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0

from datetime import timedelta
import pprint
import requests
import time

PROMETHEUS_URL = "http://127.0.0.1:9090"


class Monitoring(object):
    PROMETHEUS_HEALTH_UP = "up"
    PROMETHEUS_ISTIO_TARGETS = {"envoy",
        "istio-mesh",
        "kubernetes-apiservers",
        "kubernetes-cadvisor",
        "kubernetes-nodes",
        "kubernetes-service-endpoints",
        "mixer",
        "pilot"}
    PROMETHEUS_API_TARGETS = "/api/v1/targets"
    PROMETHEUS_API_QUERY = "/api/v1/query"
    PROMETHEUS_API_QUERY_RANGE = "/api/v1/query_range"

    def __init__(self, host):
        self.host = host

    def get_targets(self):
        try:
            # Reference api: https://prometheus.io/docs/prometheus/latest/querying/api/#targets
            response = requests.get('%s%s' % (self.host, Monitoring.PROMETHEUS_API_TARGETS))
            if response.status_code != 200:
                print("ERROR: get targets status code: %r" % response.status_code)
                return False
        except Exception as e:
            print("ERROR: Cannot connect to prometheus\n%s" % e)
            return False

        return response.json()

    def is_targets_healthy(self):
        targets = set()

        raw_targets = self.get_targets()
        if raw_targets == False:
            return False

        for target in raw_targets["data"]["activeTargets"]:
            if target["health"] != Monitoring.PROMETHEUS_HEALTH_UP:
                print("ERROR: target unhealth job: %s, health: %s" % \
                    (target["labels"]["job"], target["health"]))
                return False
            targets.add(target["labels"]["job"])

        diff = Monitoring.PROMETHEUS_ISTIO_TARGETS - targets
        if len(diff):
            print("ERROR: targets %r not found!" % diff)
            return False

        return True

    # Reference links:
    #     - https://prometheus.io/docs/prometheus/latest/querying/api/#instant-queries
    #     - https://prometheus.io/docs/prometheus/latest/querying/api/#range-queries
    #     - https://github.com/prometheus/prombench/blob/master/apps/load-generator/main.py
    def query(self, query_params):
        try:
            start = time.time()

            query_type = query_params.get("type", "instant")
            params = {"query": query_params["query"]}
            if query_type == "instant":
                url = "%s%s" % (self.host, Monitoring.PROMETHEUS_API_QUERY)
            elif query_type == "range":
                url = "%s%s" % (self.host, Monitoring.PROMETHEUS_API_QUERY_RANGE)
                params["start"] = start - duration_seconds(query_params.get("start", "0h"))
                params["end"] = start - duration_seconds(query_params.get("end", "0h"))
                params["step"] = query_params.get("step", "15s")
            else:
                print("ERROR: invalidate query type")
                return

            resp = requests.get(url, params)
            dur = time.time() - start

            print("query %s %s, status=%s, size=%d, dur=%.3f" % \
                (self.host, query_params["query"], resp.status_code, len(resp.text), dur))
            pp = pprint.PrettyPrinter(indent=2)
            ##pp.pprint(resp.json())
            return resp.json()

        except Exception as e:
            print("ERROR: Could not query prometheus instance %s. \n %s" % (url, e))


def duration_seconds(s):
    num = int(s[:-1])

    if s.endswith('s'):
        return timedelta(seconds=num).total_seconds()
    elif s.endswith('m'):
        return timedelta(minutes=num).total_seconds()
    elif s.endswith('h'):
        return timedelta(hours=num).total_seconds()

    raise "ERROR: unknown duration %s" % s


def main():
    m = Monitoring(PROMETHEUS_URL)
    if not m.is_targets_healthy():
        print("ERROR: Prometheus targets is unhealthy!")
    else:
        print("Prometheus targets are all healthy!")

    print "\n### query instant"
    query_params = {
        "type": "instant",
        "query": "istio_double_request_count{destination='details.default.svc.cluster.local'}"
    }
    m.query(query_params)

    print "\n### query range"
    query_range_param = {
        "type": "range",
        "query": "istio_double_request_count{destination='details.default.svc.cluster.local'}",
        "start": "5m",
        "end": "3m",
        "step": "30s"
     }
    m.query(query_range_param)


if __name__ == '__main__':
    main()

