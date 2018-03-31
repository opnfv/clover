# Copyright (c) Authors of Clover
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0

from kubernetes import client, config

from clover.monitoring.monitoring import Monitoring

PROMETHEUS_URL = "http://127.0.0.1:9090"
PROMETHEUS_DEPLOYMENT = "prometheus"
PROMETHEUS_LABELS = "app=prometheus"
ISTIO_NAMESPACE = "istio-system"


def validateDeploy():
    config.load_kube_config()
    appsv1 = client.AppsV1Api()
    corev1 = client.CoreV1Api()
    find_flag = False
    prom_pod_name = None

    # check prometheus deploytment
    ret = appsv1.list_deployment_for_all_namespaces(watch=False)
    for i in ret.items:
        if PROMETHEUS_DEPLOYMENT == i.metadata.name and \
           ISTIO_NAMESPACE == i.metadata.namespace:
           find_flag = True
           break
    if find_flag == False:
        print("ERROR: Deployment: {} doesn't present in {} namespace".format(
                        PROMETHEUS_DEPLOYMENT, ISTIO_NAMESPACE))
        return False

    # find prometheus pod by label selector
    ret = corev1.list_namespaced_pod(ISTIO_NAMESPACE, label_selector=PROMETHEUS_LABELS)
    for i in ret.items:
        prom_pod_name = i.metadata.name
    if prom_pod_name == None:
        print("ERROR: prometheus pod not found")
        return False

    # check prometheus pod status
    ret = corev1.read_namespaced_pod_status(prom_pod_name, ISTIO_NAMESPACE)
    if ret.status.phase != "Running":
        print("ERROR: prometheus pod %s is under %s state" % (prom_pod_name, ret.status.phase))
        return False

    return True


def validateService():
    m = Monitoring(PROMETHEUS_URL)

    return m.is_targets_healthy()


def main():
    if validateDeploy() and validateService():
        print"Prometheus monitoring validation has passed"
        return True
    else:
        print"ERROR: Prometheus monitoring validation has failed"
        return False


if __name__ == '__main__':
    main()

