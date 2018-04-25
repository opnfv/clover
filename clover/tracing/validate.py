# Copyright (c) Authors of Clover
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0

from kubernetes import client, config
import argparse

from clover.tracing.tracing import Tracing

JAEGER_DEPLOYMENT = "jaeger-deployment"
ISTIO_NAMESPACE = "istio-system"
ISTIO_SERVICES = ["istio-ingress", "istio-mixer"]


def validateDeploy():
    config.load_kube_config()
    v1 = client.AppsV1Api()

    deployments = []
    namespaces = []
    validate = False
    ret = v1.list_deployment_for_all_namespaces(watch=False)
    for i in ret.items:
        deployments.append(i.metadata.name)
        namespaces.append(i.metadata.namespace)
    if JAEGER_DEPLOYMENT in deployments:
        d_index = deployments.index(JAEGER_DEPLOYMENT)
        if ISTIO_NAMESPACE in namespaces[d_index]:
            print("Deployment: {} present in {} namespace".format(
                          JAEGER_DEPLOYMENT, ISTIO_NAMESPACE))
            validate = True
    return validate


# Services in Jaeger will only be present when traffic targets istio-ingress
# Even a failed HTTP GET request to istio-ingress will add istio-ingress and
# istio-mixer services
def validateServices(args):
    t = Tracing(args['ip'], args['port'])
    services = t.getServices()
    validate = True
    if services:
        for s in ISTIO_SERVICES:
            if s in services:
                print("Service in tracing: {} present".format(s))
            else:
                print("Service in tracing: {} not present".format(s))
                validate = False
    else:
        validate = False
    return validate


def main(args):
    vdeploy = validateDeploy()
    if args['s']:
        vservice = validateServices(args)
    else:
        vservice = True
    if vdeploy and vservice:
        print"Jaeger tracing validation has passed"
        return True
    else:
        print"Jaeger tracing validation has failed"
        return False


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
            '-s', action='store_true',
            help='Validate istio services, \
            which requires at least one http request to istio-ingress')
    parser.add_argument(
            '-ip', default='localhost',
            help='IP address to access Jaeger')
    parser.add_argument(
            '-port', default='16686',
            help='Port to acccess Jaeger')
    args = parser.parse_args()
    main(vars(args))
