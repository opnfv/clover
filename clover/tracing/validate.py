# Copyright (c) Authors of Clover
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0

from tracing import Tracing
from kubernetes import client, config


JAEGER_IP = "localhost"
# JAEGER_IP = "1.1.1.1"
JAEGER_PORT = "30888"
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


def validateServices():
    t = Tracing(JAEGER_IP, JAEGER_PORT)
    services = t.getServices()
    validate = True
    if services:
        for s in ISTIO_SERVICES:
            if s in services:
                print("Service in tracing: {} present".format(s))
            else:
                validate = False
    else:
        validate = False
    return validate


def main():
    if validateDeploy() and validateServices():
        print"Jaeger tracing validation has passed"
        return True
    else:
        print"Jaeger tracing validation has failed"
        return False


if __name__ == '__main__':
    main()
