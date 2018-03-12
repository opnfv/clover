#!/usr/bin/env python

# Copyright (c) Authors of Clover
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
import os
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
        if not routerule:  continue
        if routerule.get('kind') != 'RouteRule': continue
        ret_rr_dict = {}
        spec = routerule.get('spec')
        if not spec: continue
        ret_rr_dict['service'] = spec.get('destination').get('name')
        ret_rr_dict['rules'] = spec.get('route')
        ret_list.append(ret_rr_dict)
    return ret_list

'''
    The format of result_dict is expected to be:
    {
        'service':  <service name>,
        <version string 1>: <integer representation of version string 1 occurrances during test>,
        <version string 2>: <integer representation of version string 2 occurrances during test>,
        ...
    }
'''
def validate_weighted_route_rules(result_dict):
    svc_name = result_dict.get('service')
    rr_list = parse_route_rules(get_route_rules())
    errors = []
    for rr in rr_list:
        route_rules = rr.get('rules')
        for rule in route_rules:
            version = rule.get('labels').get('version')
            weight = rule.get('weight')
            if not weight: weight = 1
            if abs(weight - result_dict[version]) > 10:
                err = 'svc %s version %s expected to get %d, but got %d' % (svc_name, version, weight, result_dict[version])
            else:
                err = 'svc %s version %s expected to get %d, got %d. Validation succeeded' % (svc_name, version, weight, result_dict[version])
            errors.append(err)
    return errors


