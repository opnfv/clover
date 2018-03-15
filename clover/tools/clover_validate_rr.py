#!/usr/bin/env python

# Copyright (c) Authors of Clover
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0

import getopt
import sys

sys.path.insert(0, '..')

from orchestration import kube_client
import servicemesh.route_rules as rr
import tracing.tracing as tracing

def main(argv):
    # TODO(s3wong): this number should actually come from the application under test
    num_trace = 10
    service_name = None
    help_str = 'clover_validate_rr.py -n <number of traces> -s <service name>'
    try:
        opts, args = getopt.getopt(argv,"hn:s:",["num-trace=", "service-name"])
    except getopt.GetoptError:
        print help_str
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print help_str
            sys.exit()
        elif opt in ("-n", "--num-trace"):
            num_trace = int(arg)
        elif opt in ("-s", "--service-name"):
            service_name = str(arg)

    if not service_name:
        print help_str
        sys.exit(3)

    k8s_client = kube_client.KubeClient()

    istio_pods = ['istio-ingress', 'istio-mixer', 'istio-pilot']
    jaeger_pods = ['jaeger-deployment']

    for pod in istio_pods + jaeger_pods:
        up, name = k8s_client.check_pod_up(pod, 'istio-system')
        if not up:
            print('pod %s not up' % pod)
            sys.exist(4)

    trace_result_dict = tracing.count_traces(service_name, str(num_trace))
    print trace_result_dict
    result_dict = {'service': trace_result_dict.get('service')}
    total = trace_result_dict['total']
    print('total traces is %d' % total)
    if total > 0:
        results = trace_result_dict['results']
        pods = k8s_client.find_pod_by_namespace()
        for node in results:
            pod_labels = None
            for p,l in pods.items():
                if p in node:
                    pod_labels = l.get('labels')
                    break
            if not pod_labels:
                continue
            if 'version' in pod_labels:
                version_label = pod_labels.get('version')
                print('version label for node %s is %s : %d' % (node, version_label, results[node]))
                result_dict[version_label] = float(results[node]) / float(total) * 100
    print('result_dict is %s' % result_dict)
    errors = rr.validate_route_rules(result_dict)
    for err in errors:
        print err

if __name__ == "__main__":
    main(sys.argv[1:])
