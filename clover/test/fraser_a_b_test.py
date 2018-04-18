#!/usr/bin/env python

# Copyright (c) Authors of Clover
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0

import getopt
import subprocess
import sys
import time
import uuid
import yaml

#sys.path.insert(0, '..')

from clover.orchestration.kube_client import KubeClient
import clover.servicemesh.route_rules as rr
from clover.tools.validate_rr import ValidateWRR
from clover.tracing.tracing import Tracing

from validate_success import validate_perf

def _format_perf_data(perf_dict, dep_name, svc):
    in_pod= None
    out_pod = None
    out_pod_list = []
    for key, perf in perf_dict.items():
        if key == 'in':
            continue
        elif key == 'out':
            if 'out_svc' in perf:
                out_pod = perf.get('out_svc')
        elif 'out_svc' in perf:
            if perf.get('out_svc') == svc:
                in_pod = key

    if out_pod:
        out_pod_list = [key for key in perf_dict.keys() if out_pod in key.lower()]
        if out_pod_list:
            out_pod = out_pod_list[0]
            print("{: >20} {: >20} {: >20}".format(*[in_pod, dep_name] + out_pod_list))
            print("{: >20} {: >20} {: >20}".format(*[perf_dict[in_pod].get('average'),
                                                     perf_dict['in'].get('average'),
                                                     perf_dict[out_pod].get('average')]))
            return

    print("{: >20} {: >20} {: >20}".format(*[in_pod, dep_name, out_pod]))
    print("{: >20} {: >20}".format(*[perf_dict[in_pod].get('average'),
                                     perf_dict['in'].get('average')]))



def main(argv):
    test_yaml = None
    namespace = 'default'
    tracing_port = 0
    help_str = 'python fraser_a_b_test.py -t <test-yaml> -n <namespace> -p <tracing port>'
    try:
        opts, args = getopt.getopt(argv,"ht:n:p:",["test-yaml", "namespace", "tracing-port"])
    except getopt.GetoptError:
        print help_str
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print help_str
            sys.exit()
        elif opt in ("-t", "--test-yaml"):
            test_yaml = str(arg)
        elif opt in ("-n", "--namespace"):
            namespace = str(arg)
        elif opt in ("-p", "--tracing-port"):
            tracing_port = int(arg)

    if not test_yaml or tracing_port == 0:
        print help_str
        sys.exit(3)

    with open(test_yaml) as fp:
        test_params = yaml.load(fp)

    '''
    Steps:
    (1) get version one info
    (2) get version two info
    (3) start version two
    (4) validate version two pod and sidecar all up
    (5) load A-B testing route rules
    (6) execute traffic test script
    (7) validate route rules traffic distribution
    (8) validate version two success criteria
    (9) if (8) works, change to version 2 only
    (10) execute traffic test script
    (11) validate route rules traffic distribution
    '''
    APP_BASE = 'app/'
    POLICY_BASE = 'istio/'
    SCRIPT_BASE = 'script/'
    print('Current pods running at namespace %s' % namespace)
    # as this is just for display purpose, we directly use kubectl get pods
    cmd = 'kubectl get pods -n %s' % namespace
    output = subprocess.check_output(cmd, shell=True)
    print(output)

    print('Current services running at namespace %s' % namespace)
    cmd = 'kubectl get svc -n %s' % namespace
    output = subprocess.check_output(cmd, shell=True)
    print(output)

    # service under test
    test_svc = test_params.get('test-svc')
    print('Service under test: %s' % test_svc)

    k8s_client = KubeClient()
    on, _ = k8s_client.check_pod_up('istio-sidecar-injector', 'istio-system')
    print('Istio automatic sidecar injection is %s' % on)
    dep_a_name = test_params.get('deployment-A')
    dep_b = test_params.get('deployment-B')
    dep_b_name = dep_b.get('name')
    dep_b_yaml = APP_BASE + dep_b.get('manifest')
    additional_deps = test_params.get('additional-deployments')

    # TODO(s3wong): use istio-inject, then use kube_client to invoke
    dep_list = []
    print('Deploying %s...' % dep_b_name)
    if not on:
        cmd_temp = 'istioctl kube-inject -f %s > app/__tmp.yaml; kubectl apply -f app/__tmp.yaml; rm -f app/__tmp.yaml'
    else:
        cmd_temp = 'kubectl apply -f %s'

    up, _ = k8s_client.check_pod_up(dep_b_name, namespace=namespace)
    if up:
        print('%s already has pod up, no need to spawn...' % dep_b_name)
    else:
        cmd = cmd_temp % dep_b_yaml
        output = subprocess.check_output(cmd, shell=True)
        print(output)
        dep_list.append({'name': dep_b_name, 'up': False})
    if additional_deps:
        for dep in additional_deps:
            dep_name = dep.get('name')
            dep_yaml = APP_BASE + dep.get('manifest')
            up, _ = k8s_client.check_pod_up(dep_name, namespace=namespace)
            if up:
                print('%s already has pod up, no need to spawn...' % dep_name)
            else:
                cmd = cmd_temp % dep_yaml
                output = subprocess.check_output(cmd, shell=True)
                print(output)
                dep_list.append({'name': dep_name, 'up': False})

    time.sleep(3)

    wait_count = 0
    continue_waiting = False
    while wait_count < 5:
        continue_waiting = False
        for dep in dep_list:
            if not dep.get('up'):
                dep['up'], _ = k8s_client.check_pod_up(dep.get('name'), namespace=namespace)
                if not dep['up']:
                    continue_waiting = True
        if continue_waiting:
            wait_count += 1
            time.sleep(3)
        else:
            break

    if continue_waiting:
        print('Some pods are still not up after 15 seconds: %s' % dep_list)
        sys.exit(4)

    print('All pods are up')
    cmd = 'kubectl get pods -n %s' % namespace
    output = subprocess.check_output(cmd, shell=True)
    print(output)

    time.sleep(3)

    a_b_test_rr_yaml = POLICY_BASE + test_params.get('ab-test-rr')
    print('Loading route rules in %s' % a_b_test_rr_yaml)
    ret = rr.load_route_rules(a_b_test_rr_yaml)
    print('Route rules are now %s' % rr.get_route_rules())

    time.sleep(5)

    tracing = Tracing('localhost', str(tracing_port))
    # turn off tracing to redis for warm up run
    tracing.use_redis = False
    traffic_test_script = test_params.get('traffic-test')
    print('Execute traffic test %s' % traffic_test_script)
    cmd = SCRIPT_BASE + traffic_test_script
    '''
    print('Warming up for route rules to take place')
    try:
        output = subprocess.check_output(cmd, shell=True)
    except subprocess.CalledProcessError, e:
        print('%s returns error %s' % e.output)
    print(output)
    print('Running recorded traffic test...')
    '''
    time.sleep(30)
    tracing.use_redis = True
    test_id = uuid.uuid4()
    rr.set_route_rules(test_id)
    tracing.setTest(test_id)
    try:
        output = subprocess.check_output(cmd, shell=True)
    except subprocess.CalledProcessError, e:
        print('non zero return value on traffic script: %s, ignoring...' % e.output)
    print(output)
    time.sleep(30)
    traces = tracing.getTraces(test_svc, 0)
    tracing.outTraces(traces)

    time.sleep(3)
    print('Validating route rules...')
    validate_wrr = ValidateWRR(test_id)
    ret, errors = validate_wrr.validate(test_svc)

    # TODO(s3wong): for now, route rules failure seems more like a warning
    if ret:
        print('Route rules for service %s validated' % test_svc)
    else:
        print('Route rules for service %s validation failed' % test_svc)
        for err in errors:
            print err

    success_factors = test_params.get('success')
    if success_factors:
        criteria = success_factors.get('criteria')
        success_check = True
        for criterion in criteria:
            c_type = criterion.get('type')
            if c_type == 'performance':
                condition = int(criterion.get('condition'))
                ret_dict = validate_perf(tracing, test_id, test_svc,
                        dep_a_name, dep_b_name)
                # print performance data
                _format_perf_data(ret_dict.get(dep_a_name), dep_a_name, test_svc)
                print('\n')
                _format_perf_data(ret_dict.get(dep_b_name), dep_b_name, test_svc)
                ret = (ret_dict.get(dep_b_name).get('in').get('average') <= \
                      (ret_dict.get(dep_a_name).get('in').get('average') * condition / 100))
                if not ret:
                    print('Performance check failed')
                    success_check = False
                    break
                else:
                    print('Performance check succeed')
            '''
            elif c_type == 'services':
                srv_list = criterion.get('services')
                ret = check_services_traverse(tracing, test_id, test_svc,
                        dep_b_name, srv_list)
                if not ret:
                    print('Additional services traversal test failed')
                    success_check = False
                    break
                else:
                    print('Additional services traversal test succeed')
            '''
        if success_check:
            actions = success_factors.get('action')
        else:
            failed = success_factors.get('failed')
            actions = failed.get('action')
        for action in actions:
            action_type = action.get('type')
            if action_type == 'commit' or action_type == 'rollback':
                rr.delete_route_rules(a_b_test_rr_yaml, namespace)
                ret = rr.load_route_rules(POLICY_BASE + action.get('routerule'))
                if ret:
                    print('loading route rule %s succeed' % action.get('routerule'))



if __name__ == "__main__":
    main(sys.argv[1:])
