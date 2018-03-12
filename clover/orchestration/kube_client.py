#!/usr/bin/env python

# Copyright (c) Authors of Clover
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0

from kubernetes import client, config

class KubeClient(object):

    def __init__(self):
        config.load_kube_config()
        self.core_v1 = client.CoreV1Api()
        self.extensions_v1beta1 = client.ExtensionsV1beta1Api()

    def find_pod_by_namespace(self, namespace='default'):
        ret_dict = {}
        pods = self.core_v1.list_pod_for_all_namespaces(watch=False)
        if not pods:
            print('found no pod')
            return None
        for pod in pods.items:
            if pod.metadata.namespace != namespace:
                continue
            if pod.metadata.name not in ret_dict:
                ret_dict[pod.metadata.name] = {}
            ret_dict[pod.metadata.name]['labels'] = pod.metadata.labels

        return ret_dict

    def _check_pod(self, pod_name, namespace='defualt', container_name=None):
        ret = self.core_v1.list_pod_for_all_namespaces(watch=False)
        ret_code = False
        new_pod_name = None
        for i in ret.items:
            if i.metadata.namespace == namespace and pod_name in i.metadata.name:
                if i.status.container_statuses and len(i.status.container_statuses) > 0:
                    container_up = False
                    for container in i.status.container_statuses:
                        check_state = True
                        if container_name:
                            if container_name != container.name:
                                check_state = False
                        if check_state and container.state.running is not None:
                            container_up = True
                        else:
                            if container_up:
                                container_up = False
                                break
                    if container_up:
                        ret_code = True
                        new_pod_name = i.metadata.name
        return ret_code, new_pod_name

    def check_pod_up(self, pod_name, namespace='default'):
        return self._check_pod(pod_name, namespace)

    def check_container_in_pods(self, container_name, pods, namespace='default'):
        ret = False
        for pod in pods:
            ret, _ = self._check_pod(pod, namespace, container_name)
            if not ret:
                return ret
        return ret
