// Copyright (c) Authors of Clover
//
// All rights reserved. This program and the accompanying materials
// are made available under the terms of the Apache License, Version 2.0
// which accompanies this distribution, and is available at
// http://www.apache.org/licenses/LICENSE-2.0

package clovisor

import (
    "bytes"
    "fmt"
    "strconv"
    "strings"

    core_v1 "k8s.io/api/core/v1"
    "k8s.io/apimachinery/pkg/runtime"
    metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
    "k8s.io/client-go/kubernetes"
    "k8s.io/client-go/rest"
    "k8s.io/client-go/tools/remotecommand"
)

type ClovisorK8s struct {
    client      *kubernetes.Clientset
    config      *rest.Config
}

type monitoring_info_t struct {
    namespace   string
    svc_name    string
    pod_name    string
    container_name  string
    protocol    string
    port_num    uint32
}

var DEFAULT_NAMESPACE = "default"

func K8s_client_init(nodeName string) (*ClovisorK8s, error) {
    config, err := rest.InClusterConfig()
    if err != nil {
        fmt.Println(err.Error())
        return nil, err
    }

    client, err := kubernetes.NewForConfig(config)
    if err != nil {
        fmt.Println(err.Error())
        return nil, err
    }

    return &ClovisorK8s{
        client:     client,
        config:     config,
    }, nil
}

func parse_label_cfg(label_cfg string) (string, string, string) {
    label_slice := strings.Split(label_cfg, ":")
    if len(label_slice) == 1 {
        return label_slice[0], "", ""
    }
    return label_slice[0], label_slice[1], label_slice[2]
}

func (client *ClovisorK8s) Get_monitoring_info(nodeName string) (map[string]*monitoring_info_t,
                                               error) {

    labels_list, err := get_cfg_labels(nodeName)
    if err != nil {
        fmt.Printf("Error getting cfg labels: %v\n", err)
        return nil, err
    }

    namespace, svcs, pods, err := client.fetch_svcs_pods(nodeName, labels_list)
    if err != nil {
        return nil, err
    }

    mon_info_map := make(map[string]*monitoring_info_t)
    for idx, _ := range svcs {
        svc := svcs[idx]
        pod := pods[idx]
        mon_info := client.get_monitoring_pods(namespace, nodeName, svc, pod)
        for k, v := range mon_info {
            mon_info_map[k] = v
        }
    }
    return mon_info_map, nil
}

func (client *ClovisorK8s) fetch_svcs_pods(nodeName string,
                                           labels_list []string) (string,
                                                                  []*core_v1.ServiceList,
                                                                  []*core_v1.PodList, error) {
    namespace := DEFAULT_NAMESPACE
    /*
     * Three cases:
     * 1.) no configured namespaces, monitoring all pods in default namesapce
     * 2.) if any config only has namespace, monitoring all pods in namespace
     * 3.) label is configured, only monitor pods with that label
     */
    var svcs []*core_v1.ServiceList
    var pods []*core_v1.PodList
    if len(labels_list) == 0 {
        if svcs_list, err :=
            client.client.CoreV1().Services(namespace).List(metav1.ListOptions{});
                        err != nil {
            fmt.Printf("Error fetching service list for namespace %s\n",
                        namespace)
            return namespace, nil, nil, err
        } else {
            svcs = append(svcs, svcs_list)
        }

        if pods_list, err :=
            client.client.CoreV1().Pods(namespace).List(metav1.ListOptions{});
                        err != nil {
            fmt.Printf("Error fetching pods list for namespace %s\n",
                        namespace)
            return namespace, nil, nil, err
        } else {
            pods = append(pods, pods_list)
        }
    } else {
        for _, label_str := range labels_list {
            var label_selector string
            namespace, key, value := parse_label_cfg(label_str)
            if len(namespace) == 0 {
                fmt.Printf("Error in config: %s not a valid config\n", label_str)
                continue
            }
            if len(key) == 0 {
                fmt.Printf("Namespace only config for %s\n", namespace)
            } else {
                label_selector = fmt.Sprintf("%s=%s", key, value)
            }
            if svc_list, err :=
                    client.client.CoreV1().Services(namespace).List(metav1.ListOptions{
                        LabelSelector: label_selector,
                                }); err != nil {
                fmt.Printf("Error listing services with label %v:%v:%v - %v\n",
                            key, value, namespace, err.Error())
                continue
            } else {
                svcs = append(svcs, svc_list)
            }
            if pod_list, err :=
                client.client.CoreV1().Pods(namespace).List(metav1.ListOptions{
                        LabelSelector: label_selector,
                                }); err != nil {
                fmt.Printf("Error listing pods with label %v:%v:%v - %v\n",
                            key, value, namespace, err.Error())
                continue
            } else {
                pods = append(pods, pod_list)
            }
        }
    }
    return namespace, svcs, pods, nil
}

func (client *ClovisorK8s) get_monitoring_pods(
                    namespace string,
                    node_name string,
                    svcs *core_v1.ServiceList,
                    pods *core_v1.PodList) (map[string]*monitoring_info_t) {
    monitoring_info := make(map[string]*monitoring_info_t)
    svc_map := make(map[string][]string)

    for _, svc := range svcs.Items {
        svc_port := svc.Spec.Ports[0]
        target_port := svc_port.TargetPort.String()
        svc_port_name := svc_port.Name
        svc_map[target_port] = append(svc_map[target_port], svc.GetName())
        if len(svc_port_name) > 0 {
            svc_map[target_port] = append(svc_map[target_port], svc_port_name)
        } else {
            svc_map[target_port] = append(svc_map[target_port], "tcp")
        }
    }
    for _, v := range pods.Items {
        if v.Spec.NodeName == node_name {
            pod_name := v.GetName()
            monitoring_info[pod_name] = &(monitoring_info_t{})
            monitoring_info[pod_name].namespace = namespace
            monitoring_info[pod_name].pod_name = pod_name
            monitoring_info[pod_name].container_name = v.Spec.Containers[0].Name
            monitoring_info[pod_name].port_num = uint32(v.Spec.Containers[0].Ports[0].ContainerPort)
            tp_string := strconv.Itoa(int(monitoring_info[pod_name].port_num))
            svc_array := svc_map[tp_string]
            monitoring_info[pod_name].svc_name = svc_array[0]
            if (strings.Contains(svc_array[1], "-")) {
                monitoring_info[pod_name].protocol = svc_array[1][:strings.Index(svc_array[1], "-")]
            } else {
                monitoring_info[pod_name].protocol = svc_array[1]
            }
        }
    }
    return monitoring_info
}

func (client *ClovisorK8s) exec_command(command string,
                                        monitoring_info *monitoring_info_t) (string, error) {

    // Following code based on:
    // https://stackoverflow.com/questions/43314689/example-of-exec-in-k8ss-pod-by-using-go-client
    // https://github.com/a4abhishek/Client-Go-Examples/blob/master/exec_to_pod/exec_to_pod.go
    exec_req := client.client.CoreV1().RESTClient().Post().
            Resource("pods").
            Name(monitoring_info.pod_name).
            Namespace(monitoring_info.namespace).
            SubResource("exec")
    scheme := runtime.NewScheme()
    if err := core_v1.AddToScheme(scheme); err != nil {
        fmt.Printf("Error in exec pods: %v\n", err.Error())
        return "", err
    }

    parameterCodec := runtime.NewParameterCodec(scheme)
    exec_req.VersionedParams(&core_v1.PodExecOptions{
            Command:    strings.Fields(command),
            Container:  monitoring_info.container_name,
            Stdin:      false,
            Stdout:     true,
            Stderr:     true,
            TTY:        false,
        }, parameterCodec)

    exec, err := remotecommand.NewSPDYExecutor(client.config, "POST", exec_req.URL())
    if err != nil {
        fmt.Printf("Error in remotecommand exec: %v\n", err.Error())
        return "", err
    }

    var stdout, stderr bytes.Buffer
    err = exec.Stream(remotecommand.StreamOptions{
            Stdin:  nil,
            Stdout: &stdout,
            Stderr: &stderr,
            Tty:    false,
        })
    if err != nil {
        fmt.Printf("Error in exec stream: %v\n", err.Error())
        return "", err
    }

    stdout_no_newline := strings.TrimSuffix(stdout.String(), "\n")
    return stdout_no_newline, nil
}
