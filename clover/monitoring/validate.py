# Copyright (c) Authors of Clover
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0

import requests

PROMETHEUS_URL = "http://127.0.0.1:9090"
PROMETHEUS_HEALTH_UP = "up"
PROMETHEUS_ISTIO_TARGETS = {"envoy",
    "istio-mesh",
    "kubernetes-apiservers",
    "kubernetes-cadvisor",
    "kubernetes-nodes",
    "kubernetes-service-endpoints",
    "mixer",
    "pilot"}

def is_targets_healthy(url, istio_targets):
    targets = set()
    # https://prometheus.io/docs/prometheus/latest/querying/api/#targets
    response = requests.get('{0}/api/v1/targets'.format(url))
    if response.status_code != 200:
        print("ERROR: get targets status code: %r" % response.status_code)
        return False

    results = response.json()
    for target in results["data"]["activeTargets"]:
        if target["health"] != PROMETHEUS_HEALTH_UP:
            print("ERROR: target unhealth job: %s, health: %s" % \
                (target["labels"]["job"], target["health"]))
            return False
        targets.add(target["labels"]["job"])

    diff = istio_targets - targets
    if len(diff):
        print("ERROR: targets %r not found!" % diff)
        return False

    return True

def main():
    if not is_targets_healthy(PROMETHEUS_URL, PROMETHEUS_ISTIO_TARGETS):
        print("ERROR: Prometheus targets is unhealthy!")
    else:
        print("Prometheus targets are all healthy!")

if __name__ == '__main__':
    main()

