#!/usr/bin/env python

# Copyright (c) Authors of Clover
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0

import getopt
import sys

from clover.orchestration import kube_client
import clover.servicemesh.route_rules as rr
from clover.tracing.tracing import Tracing
from clover.tools.validate_rr import ValidateWRR

def main(argv):
    service_name = None
    test_id = None
    help_str = 'clover_validate_rr.py -t <test-id> -s <service name>'
    try:
        opts, args = getopt.getopt(argv,"hs:t:",["service-name", "test-id"])
    except getopt.GetoptError:
        print help_str
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print help_str
            sys.exit()
        elif opt in ("-t", "--test-id"):
            test_id = str(arg)
        elif opt in ("-s", "--service-name"):
            service_name = str(arg)

    if not service_name or not test_id:
        print help_str
        sys.exit(3)

    validate_wrr = ValidateWRR(test_id)

    istio_pods = ['istio-ingress', 'istio-mixer', 'istio-pilot']
    jaeger_pods = ['jaeger-deployment']

    if not validate_wrr.check_pods_up(istio_pods + jaeger_pods,
                                      'istio-system'):
        sys.exit(4)

    ret, errors = validate_wrr.validate(service_name)
    for err in errors:
        print err

if __name__ == "__main__":
    main(sys.argv[1:])
