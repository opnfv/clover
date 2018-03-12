#!/usr/bin/env python

# Copyright (c) Authors of Clover
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
import os
import redis
import subprocess
import sys
import yaml

#istioctl='$HOME/istio-0.6.0/bin/istioctl'
# The assumption is that istioctl is already in the user's path
ISTIOCTL='istioctl'

def cmd_exists(cmd):
    return any(
        os.access(os.path.join(path, cmd), os.X_OK)
        for path in os.environ["PATH"].split(os.pathsep)
    )

def load_route_rules(rr_yaml_path):
    if not cmd_exists(ISTIOCTL):
        print('%s does not exist in PATH, please export istioctl to PATH' % istioctl)
        return False

    # TODO(s3wong): load yaml and verify it does indeed contain route rule
    cmd = ISTIOCTL + ' create -f ' + rr_yaml_path
    output = subprocess.check_output(cmd, shell=True)
    if not output:
        print('Route rule creation failed: %s' % output)
        return False
    return True

def delete_route_rules(rr_yaml_path, namespace):
    if not cmd_exists(ISTIOCTL):
        print('%s does not exist in PATH, please export istioctl to PATH' % istioctl)
        return False

    # TODO(s3wong): load yaml and verify it does indeed contain route rule
    cmd = ISTIOCTL + ' delete -f ' + rr_yaml_path + ' -n ' + namespace
    output = subprocess.check_output(cmd, shell=True)
    if not output or not 'Deleted' in output:
        print('Route rule deletion failed: %s' % output)
        return False
    return True

def get_route_rules():
    if not cmd_exists(ISTIOCTL):
        print('%s does not exist in PATH, please export istioctl to PATH' % istioctl)
        return None
    cmd = ISTIOCTL + ' get routerules -o yaml'
    output = subprocess.check_output(cmd, shell=True)
    if not output:
        print('No route rule configured')
        return None
    docs = []
    for raw_doc in output.split('\n---'):
        try:
            docs.append(yaml.load(raw_doc))
        except SyntaxError:
            print('syntax error: %s' % raw_doc)
    return docs

def parse_route_rules(routerules):
    ret_list = []
    if not routerules:
        print('No routerules')
        return ret_list
    for routerule in routerules:
        if not routerule or routerule == 'None':  continue
        print('routerule is %s' % routerule)
        if routerule.get('kind') != 'RouteRule': continue
        ret_rr_dict = {}
        spec = routerule.get('spec')
        if not spec: continue
        ret_rr_dict['service'] = spec.get('destination').get('name')
        ret_rr_dict['rules'] = spec.get('route')
        ret_list.append(ret_rr_dict)
    return ret_list

def _derive_key_from_test_id(test_id):
    return 'route-rules-' + str(test_id)

def set_route_rules(test_id):
    r = redis.StrictRedis(host='localhost', port=6379, db=0)
    key = _derive_key_from_test_id(test_id)
    rr = get_route_rules()
    r.set(key, rr)

def fetch_route_rules(test_id):
    r = redis.StrictRedis(host='localhost', port=6379, db=0)
    key = _derive_key_from_test_id(test_id)
    rr = r.get(key)
    return yaml.load(rr)

'''
    The format of result_dict is expected to be:
    {
        'service':  <service name>,
        <version string 1>: <integer representation of version string 1 occurrances during test>,
        <version string 2>: <integer representation of version string 2 occurrances during test>,
        ...
    }
'''
def validate_weighted_route_rules(result_dict, test_id=None):
    print('validate_weighted_route_rules: test id %s' % test_id)
    svc_name = result_dict.get('service')
    if not test_id:
        rr_list = parse_route_rules(get_route_rules())
    else:
        rr_list = parse_route_rules(fetch_route_rules(test_id))
    errors = []
    ret = True
    for rr in rr_list:
        route_rules = rr.get('rules')
        if not route_rules:
            break
        for rule in route_rules:
            version = rule.get('labels').get('version')
            weight = rule.get('weight')
            if not weight: weight = 1
            if abs(weight - result_dict[version]) > 10:
                err = 'svc %s version %s expected to get %d, but got %d' % (svc_name, version, weight, result_dict[version])
                ret = False
            else:
                err = 'svc %s version %s expected to get %d, got %d. Validation succeeded' % (svc_name, version, weight, result_dict[version])
            errors.append(err)
    return ret, errors


