#!/usr/bin/env python

# Copyright (c) Authors of Clover
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
import sys

sys.path.insert(0, '..')

from orchestration import kube_client
import servicemesh.route_rules as rr
from tracing.tracing import Tracing

class ValidateWRR(object):

    def __init__(self, test_id, tracing_ip='localhost', tracing_port='31298'):
        self._k8s_client = kube_client.KubeClient()
        self._test_id = test_id
        self._tracing = Tracing(tracing_ip, tracing_port)

    def check_pods_up(self, pod_list, namespace='default'):
        for pod in pod_list:
            up, name = self._k8s_client.check_pod_up(pod, namespace)
            if not up:
                print('pod %s in namespace %s not up' % (pod, namespace))
                return False
        return True

    def set_test_id(self, test_id):
        self._test_id = test_id

    def validate(self, service_name):
        total = 0
        svc = self._k8s_client.find_svc_by_namespace(svc_name=service_name)
        if not svc:
            err_msg = 'Failed to locate service %s in default namespace' % service_name
            print err_msg
            return False, [err_msg]
        pods = self._k8s_client.find_pod_by_namespace()
        if not pods:
            err_msg = 'No pod found in default namespace'
            return False, [err_msg]
        svc_pods = {}
        for p,l in pods.items():
            pod_labels = l.get('labels')
            svc_selector_dict = svc[service_name].get('selector')
            for svc_select_key in svc_selector_dict:
                if svc_select_key in pod_labels:
                    if svc_selector_dict[svc_select_key] == pod_labels[svc_select_key]:
                        svc_pods[p] = l

        trace_ids = self._tracing.getRedisTraceids(self._test_id)
        rr_dict = {'service': service_name}
        ver_count_dict = {}
        for trace_id in trace_ids:
            span_ids = self._tracing.getRedisSpanids(trace_id)
            for span in span_ids:
                # count only the received side --- i.e., messages sent TO
                # service
                node_id = self._tracing.getRedisTagsValue(span, trace_id, 'node_id')
                direction = self._tracing.getRedisTagsValue(span, trace_id, 'upstream_cluster')
                if direction.startswith('in.'):
                    for pod_name in svc_pods:
                        if pod_name in node_id:
                            total += 1
                            labels = svc_pods[pod_name]['labels']
                            print('node %s pod %s labels %s' % (node_id, pod_name, labels))
                            if 'version' in labels:
                                version = labels.get('version')
                                if version in ver_count_dict:
                                    ver_count_dict[version] += 1
                                else:
                                    ver_count_dict[version] = 1

        print('total is %d, ver_count_dict is %s' % (total, ver_count_dict))
        if ver_count_dict and total > 0:
            for version in ver_count_dict:
                rr_dict[version] = float(ver_count_dict[version]) / float(total) * 100

            return(rr.validate_weighted_route_rules(rr_dict, self._test_id))
        else:
            err_msg = 'No version label found on any pod'
            print(err_msg)
            return False, [err_msg]

