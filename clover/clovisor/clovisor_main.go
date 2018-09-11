// Copyright (c) Authors of Clover
//
// All rights reserved. This program and the accompanying materials
// are made available under the terms of the Apache License, Version 2.0
// which accompanies this distribution, and is available at
// http://www.apache.org/licenses/LICENSE-2.0

package main

import (
    "fmt"
    "os"
    "os/signal"

    clovisor "./libclovisor"
)

var podMonitoringMap map[string]*clovisor.ClovisorBCC

func main() {
    node_name := os.Getenv("MY_NODE_NAME")

    podMonitoringMap = make(map[string]*clovisor.ClovisorBCC)

    clovisor_k8s_client, err := clovisor.K8s_client_init(node_name)
    if err != nil {
        fmt.Printf("Clovisor to Kubernetes connectivity failed: %v\n", err)
        return
    }
    fmt.Printf("Clovisor got k8s client succeed\n")

    monitoring_info_map, err := clovisor_k8s_client.Get_monitoring_info(node_name)
    if err != nil {
        fmt.Printf("Clovisor getting monitoring info failed: %v\n", err)
        return
    }
    fmt.Printf("Clovisor get monitoring info succeed: %v\n", monitoring_info_map)

    for pod := range monitoring_info_map {
        podMon, err := clovisor.ClovisorNewPodInit(clovisor_k8s_client, pod,
                                                   monitoring_info_map[pod])
        if err != nil {
            fmt.Printf("Clovisor monitoring pod %s failed: %v\n", pod, err)
            continue
        }
        podMonitoringMap[pod] = podMon
    }
    sig := make(chan os.Signal, 1)
    signal.Notify(sig, os.Interrupt, os.Kill)
    <-sig
}

