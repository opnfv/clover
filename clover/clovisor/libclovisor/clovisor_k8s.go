// Copyright (c) Authors of Clover
//
// All rights reserved. This program and the accompanying materials
// are made available under the terms of the Apache License, Version 2.0
// which accompanies this distribution, and is available at
// http://www.apache.org/licenses/LICENSE-2.0

package clovisor

import (
    "bytes"
    "errors"
    "fmt"
    "strconv"
    "strings"

    core_v1 "k8s.io/api/core/v1"
    metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
    "k8s.io/apimachinery/pkg/labels"
    "k8s.io/apimachinery/pkg/runtime"
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
    protocols   []string
    port_num    uint32
    pod_ip      string
}

var DEFAULT_NAMESPACE = "default"
var SUPPORTED_PROTOCOLS = [...]string {"tcp", "http"}

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

    mon_info_map := client.get_monitoring_pods(nodeName, labels_list)
    if mon_info_map == nil {
        return nil, errors.New("monitoring info empty")
    }

    return mon_info_map, nil
}

func (client *ClovisorK8s) getPodsForSvc(svc *core_v1.Service,
                                         namespace string) (*core_v1.PodList, error) {
    set := labels.Set(svc.Spec.Selector)
    //label := strings.Split(set.AsSelector().String(), ",")[0]
    //fmt.Printf("Trying to get pods for service %v with label %v from %v\n", svc.GetName(), label, set.AsSelector().String())
    listOptions := metav1.ListOptions{LabelSelector: set.AsSelector().String()}
    //listOptions := metav1.ListOptions{LabelSelector: label}
    return client.client.CoreV1().Pods(namespace).List(listOptions)
}

func (client *ClovisorK8s) get_monitoring_pods(nodeName string,
                                               labels_list []string) (map[string]*monitoring_info_t) {
    /*
     * Three cases:
     * 1.) no configured namespaces, monitoring all pods in default namesapce
     * 2.) if any config only has namespace, monitoring all pods in namespace
     * 3.) label is configured, only monitor pods with that label
     */
    var namespace string
    ns_svc_map := make(map[string][]*core_v1.ServiceList)
    monitoring_info := make(map[string]*monitoring_info_t)
    if len(labels_list) == 0 {
        // TODO(s3wong): set it to 'default'
        //namespace = "linux-foundation-gke"
        namespace = "default"
        if svcs_list, err :=
            client.client.CoreV1().Services(namespace).List(metav1.ListOptions{});
                        err != nil {
            fmt.Printf("Error fetching service list for namespace %s\n",
                        namespace)
            return nil
        } else {
            /*
            if _, ok := ns_svc_map[namespace]; !ok {
                ns_svc_map[namespace] = []*core_v1.ServiceList{}
            }
            */
            ns_svc_map[namespace] = append(ns_svc_map[namespace], svcs_list)
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
                if _, ok := ns_svc_map[namespace]; !ok {
                    ns_svc_map[namespace] = []*core_v1.ServiceList{}
                }
                ns_svc_map[namespace] = append(ns_svc_map[namespace], svc_list)
            }
        }
    }

    for ns, svc_slice := range ns_svc_map {
        for _, svc_list_ := range svc_slice {
            for _, svc := range svc_list_.Items {
                if ns == "default" && svc.GetName() == "kubernetes" {
                    continue
                }
                //fmt.Printf("Looking for supported protocols for service %v:%v\n", ns, svc.GetName())
                //var svc_port_map = map[string]core_v1.ServicePort{}
                var svc_port_map = map[string][]string{}
                for _, svc_port := range svc.Spec.Ports {
                    if len(svc_port.Name) > 0 {
                        svc_protos := strings.Split(svc_port.Name, "-")
                        for _, proto := range svc_protos {
                            if err := loadProtoParser(proto, false); err == nil {
                                for _, sp := range SUPPORTED_PROTOCOLS {
                                    if strings.Contains(proto, sp) {
                                        target_port := svc_port.TargetPort.String()
                                        svc_port_map[target_port] = append(svc_port_map[target_port], proto)
                                    }
                                }
                            } else {
                                fmt.Printf("Unsupported protocol: %v\n", proto)
                            }
                        }
                    }
                }
                if len(svc_port_map) == 0 {
                    fmt.Printf("Found no port with supported protocol for %v:%v\n", ns, svc.GetName())
                    continue
                } else {
                    fmt.Printf("svc_port_map for service %v is %v\n", svc.GetName(), svc_port_map)
                }
                //fmt.Printf("Fetching pods for namespace %v service: %v\n", ns, svc.GetName())
                pod_list, err := client.getPodsForSvc(&svc, ns)
                if err != nil {
                    fmt.Print("Error fetching pods for %v:%v [%v]\n", ns, svc.GetName(), err)
                    continue
                }
                /*
                labelSet := labels.Set(svc.Spec.Selector)
                pod_list, err := client.client.CoreV1().Pods(ns).List(metav1.ListOptions{})
                if err != nil {
                    fmt.Print("Error fetching pods for %v:%v [%v]\n", ns, svc.GetName(), err)
                    continue
                }
                */
                for _, pod := range pod_list.Items {
                    if pod.Spec.NodeName == nodeName {
                        for _, container := range pod.Spec.Containers {
                            var port_num uint32
                            var tp_string string
                            for _, port := range container.Ports {
                                port_num = uint32(port.ContainerPort)
                                tp_string = strconv.Itoa(int(port_num))
                                if _, in := svc_port_map[tp_string]; !in {
                                    continue
                                }
                                pod_name := pod.GetName()
                                monitoring_info[pod_name] = &(monitoring_info_t{})
                                monitoring_info[pod_name].namespace = ns
                                monitoring_info[pod_name].svc_name = svc.GetName()
                                monitoring_info[pod_name].pod_name = pod_name
                                monitoring_info[pod_name].container_name = container.Name
                                monitoring_info[pod_name].port_num = port_num
                                monitoring_info[pod_name].protocols = svc_port_map[tp_string]
                                monitoring_info[pod_name].pod_ip = pod.Status.PodIP
                            }
                        }
                    }
                }
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
