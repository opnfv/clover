#!/usr/bin/env python

# Copyright (c) Authors of Clover
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
from clover.orchestration import kube_client
from clover.tracing.tracing import Tracing

def _get_svc_pods(svc_name, namespace):
    k8s_client = kube_client.KubeClient()
    svc = k8s_client.find_svc_by_namespace(svc_name=svc_name,
                                           namespace=namespace)
    if not svc:
        err_msg = 'Failed to locate service %s in %s namespace' \
                  % (svc_name, namespace)
        print err_msg
        return False, [err_msg]
    pods = k8s_client.find_pod_by_namespace()
    if not pods:
        err_msg = 'No pod found in namespace %s' % namespace
        return False, [err_msg]
    svc_pods = {}
    for p,l in pods.items():
        pod_labels = l.get('labels')
        svc_selector_dict = svc[service_name].get('selector')
        for svc_select_key in svc_selector_dict:
            if svc_select_key in pod_labels:
                if svc_selector_dict[svc_select_key] == pod_labels[svc_select_key]:
                    svc_pods[p] = l
    return svc_pods

def validate_perf(tracing, test_id, svc_name, control_svc, variant_svc):
    ret_dict = {}
    ret_dict[control_svc] = {}
    ret_dict[control_svc]['in'] = {}
    ret_dict[control_svc]['in']['total'] = 0
    ret_dict[control_svc]['in']['average'] = 0
    ret_dict[control_svc]['out'] = {}
    ret_dict[control_svc]['out']['total'] = 0
    ret_dict[control_svc]['out']['average'] = 0

    ret_dict[variant_svc] = {}
    ret_dict[variant_svc]['in'] = {}
    ret_dict[variant_svc]['in']['total'] = 0
    ret_dict[variant_svc]['in']['average'] = 0
    ret_dict[variant_svc]['out'] = {}
    ret_dict[variant_svc]['out']['total'] = 0
    ret_dict[variant_svc]['out']['average'] = 0

    req_id_dict = {}
    def _fill_up_ret_dict(direction, svc, duration, out_svc=None):
        sum = ret_dict[svc][direction]['average'] * \
              ret_dict[svc][direction]['total'] + \
              int(duration)
        ret_dict[svc][direction]['total'] += 1
        ret_dict[svc][direction]['average'] = \
            float(sum) / float(ret_dict[svc][direction]['total'])
        if direction == 'out' and out_svc:
            # tracking the out service from svc
            # TODO(s3wong): this assumes only ONE direction from
            # service to another service, which may not be true
            # in essence, the data structure should track (srv, out)
            # pairs and calculate average that way
            ret_dict[svc][direction]['out_svc'] = out_svc


    def _check_req_id(req_id, svc=None, node_id=None,
                      duration=None, direction=None,
                      out_svc=None):
        if req_id not in req_id_dict:
            req_id_dict[req_id] = {}

        if svc:
            req_id_dict[req_id]['svc'] = svc
        else:
            req_id_dict[req_id]['node_id'] = node_id
            req_id_dict[req_id]['duration'] = int(duration)
            req_id_dict[req_id]['direction'] = direction
            if direction == 'out' and out_svc:
                req_id_dict[req_id]['out_svc'] = out_svc

    trace_ids = tracing.getRedisTraceids(test_id)
    for trace_id in trace_ids:
        span_ids = tracing.getRedisSpanids(trace_id)
        for span in span_ids:
            out_svc = None
            duration = tracing.getRedisSpanValue(span, trace_id, 'duration')
            node_id = tracing.getRedisTagsValue(span, trace_id, 'node_id')
            upstream_cluster = tracing.getRedisTagsValue(span, trace_id, 'upstream_cluster')
            req_id = tracing.getRedisTagsValue(span, trace_id, 'guid:x-request-id')
            if upstream_cluster.startswith('in.'):
                direction = 'in'
            else:
                direction = 'out'
                out_svc = upstream_cluster.split('.')[1]
            if control_svc in node_id:
                _fill_up_ret_dict(direction, control_svc, duration, out_svc=out_svc)
                _check_req_id(req_id, svc=control_svc)
            elif variant_svc in node_id:
                _fill_up_ret_dict(direction, variant_svc, duration, out_svc=out_svc)
                _check_req_id(req_id, svc=variant_svc)
            else:
                # client to svc or server from svc as client
                if out_svc and out_svc == svc_name:
                    _check_req_id(req_id, node_id=node_id, direction=direction,
                                  duration=duration, out_svc=out_svc)

    for req_id, svc_dict in req_id_dict.items():
        node_id = svc_dict.get('node_id')
        if not node_id:
            continue
        pod_name = node_id.split('~')[2]
        svc = svc_dict.get('svc')
        if pod_name not in ret_dict.get(svc):
            ret_dict[svc][pod_name] = {}
            ret_dict[svc][pod_name]['total'] = 0
            ret_dict[svc][pod_name]['direction'] = svc_dict.get('direction')
            if svc_dict.get('out_svc'):
                ret_dict[svc][pod_name]['out_svc'] = svc_dict.get('out_svc')
            ret_dict[svc][pod_name]['average'] = 0
        sum = ret_dict[svc][pod_name]['average'] * \
              ret_dict[svc][pod_name]['total'] + \
              svc_dict.get('duration')
        ret_dict[svc][pod_name]['total'] += 1
        ret_dict[svc][pod_name]['average'] = \
            float(sum) / float(ret_dict[svc][pod_name]['total'])

    return ret_dict
