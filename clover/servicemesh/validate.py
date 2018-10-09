#!/usr/bin/env python

# Copyright (c) Authors of Clover
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0

from kubernetes import client, config

ISTIO_NAMESPACE = "istio-system"
ISTIO_DEPLOYMENT = "istio-pilot"


def validateDeploy():
    config.load_kube_config()
    appsv1 = client.AppsV1Api()
    corev1 = client.CoreV1Api()
    find_flag = False

    # check deploytment
    ret = appsv1.list_deployment_for_all_namespaces(watch=False)
    for i in ret.items:
        if ISTIO_DEPLOYMENT == i.metadata.name and \
           ISTIO_NAMESPACE == i.metadata.namespace:
           find_flag = True
           break
    if find_flag == False:
        print("ERROR: Deployment: {} doesn't present in {} namespace".format(
                        ISTIO_DEPLOYMENT, ISTIO_NAMESPACE))
        return False

    return True


def main():
    if validateDeploy():
        print"Istio install validation has passed"
        return True
    else:
        print"ERROR: Istio install validation has failed"
        return False


if __name__ == '__main__':
    main()
