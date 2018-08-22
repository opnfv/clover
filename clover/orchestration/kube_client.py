# Copyright (c) Authors of Clover
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0

from os import path
import yaml

from kubernetes import client, config
from kubernetes.stream import stream

class KubeClient(object):

    def __init__(self):
        config.load_kube_config()
        self.core_v1 = client.CoreV1Api()
        self.extensions_v1beta1 = client.ExtensionsV1beta1Api()

    def find_svc_by_namespace(self, svc_name, namespace='default'):
        ret_dict = {}
        try:
            svc = self.core_v1.read_namespaced_service(name=svc_name,
                                                       namespace=namespace)
        except client.rest.ApiException:
            svc = None
        if not svc:
            print('found no service %s in namespace %s' \
                   % (svc_name, namespace))
            return None
        ret_dict[svc.metadata.name] = {}
        ret_dict[svc.metadata.name]['labels'] = svc.metadata.labels
        ret_dict[svc.metadata.name]['selector'] = svc.spec.selector
        ret_dict[svc.metadata.name]['cluster_ip'] = svc.spec.cluster_ip

        return ret_dict

    def find_pod_by_name(self, pod_name, namespace='default'):
        ret_dict = {}
        try:
            pod = self.core_v1.read_namespaced_pod(name=pod_name,
                                                   namespace=namespace)
        except client.rest.ApiException:
            pod = None
        if not pod:
            print('found no pod %s in namespace %s' \
                   % (pod_name, namespace))
            return None
        ret_dict['name'] = pod_name
        ret_dict['labels'] = pod.metadata.labels
        ret_dict['pod_ip'] = pod.status.pod_ip

        return ret_dict


    def find_pod_by_namespace(self, namespace='default'):
        ret_dict = {}
        pods = self.core_v1.list_namespaced_pod(namespace=namespace)
        if not pods:
            print('found no pod')
            return None
        for pod in pods.items:
            if pod.metadata.name not in ret_dict:
                ret_dict[pod.metadata.name] = {}
            ret_dict[pod.metadata.name]['labels'] = pod.metadata.labels

        return ret_dict

    def _check_pod(self, pod_name, namespace='defualt', container_name=None):
        ret = self.core_v1.list_namespaced_pod(namespace=namespace)
        ret_code = False
        new_pod_name = None
        for i in ret.items:
            if pod_name in i.metadata.name:
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

    def create_deployment_yaml(self, deployment_yaml_path, namespace='default'):
        with open(deployment_yaml_path) as fp:
            body = yaml.load(fp)
            resp = self.extensions_v1beta1.create_namespaced_deployment(
                    body=body, namespace=namespace)
            print('Deployment created. Status=%s' % str(resp.status))

            dep_name = body.get('metadata').get('name')
            return dep_name

    def create_service_yaml(self, service_yaml_path, namespace='default'):
        with open(service_yaml_path) as fp:
            body = yaml.load(fp)
            resp = self.extensions_v1beta1.create_namespaced_service(
                    body=body, namespace=namespace)
            print('Service created. Status=%s' % str(resp.status))

            svc_name = body.get('metadata').get('name')
            return svc_name

    def copy_file_to_pod(self, source, destination, podname, namespace='default'):
        # Note: only can copy file to the pod, which only include on container
        exec_command = ['/bin/sh']
        resp = stream(self.core_v1.connect_get_namespaced_pod_exec, podname,
                      namespace,
                      command=exec_command,
                      stderr=True, stdin=True,
                      stdout=True, tty=False,
                      _preload_content=False)

        buffer = ''
        with open(source, "rb") as file:
            buffer += file.read()

        commands = []
        commands.append(bytes("cat <<'EOF' >" + destination + "\n"))
        commands.append(buffer)
        commands.append(bytes("EOF\n"))

        while resp.is_open():
            resp.update(timeout=1)
            if resp.peek_stdout():
                print("STDOUT: %s" % resp.read_stdout())
            if resp.peek_stderr():
                print("STDERR: %s" % resp.read_stderr())
            if commands:
                c = commands.pop(0)
                resp.write_stdin(c)
            else:
                break

        resp.close()
