// Copyright (c) Authors of Clover
//
// All rights reserved. This program and the accompanying materials
// are made available under the terms of the Apache License, Version 2.0
// which accompanies this distribution, and is available at
// http://www.apache.org/licenses/LICENSE-2.0

package cmd

import (
    "fmt"
    "github.com/spf13/cobra"
    "cloverkube"
)

var delsystemCmd = &cobra.Command{
    Use:   "system",
    Short: "Delete clover-system in Kubernetes",
    Long: ``,
    Run: func(cmd *cobra.Command, args []string) {
        delCloverSystem("controller")
    },
}

var del_controllerCmd = &cobra.Command{
    Use:   "controller",
    Short: "Delete controller service from clover-system namespace",
    Long: ``,
    Run: func(cmd *cobra.Command, args []string) {
        fmt.Println("Deleting controller service")
        delCloverSystem("controller")
    },
}

var del_controllernodeportCmd = &cobra.Command{
    Use:   "nodeport",
    Short: "Delete controller nodeport service from clover-system namespace",
    Long: ``,
    Run: func(cmd *cobra.Command, args []string) {
        fmt.Println("Deleting nodeport for controller service")
        delCloverSystem("controller_nodeport")
    },
}

var del_controllerlbCmd = &cobra.Command{
    Use:   "lb",
    Short: "Delete controller lb service from clover-system namespace",
    Long: ``,
    Run: func(cmd *cobra.Command, args []string) {
        fmt.Println("Deleting lb for controller service")
        delCloverSystem("controller_lb")
    },
}

var del_collectorCmd = &cobra.Command{
    Use:   "collector",
    Short: "Delete collector service from clover-system namespace",
    Long: ``,
    Run: func(cmd *cobra.Command, args []string) {
        fmt.Println("Deleting collector service")
        delCloverSystem("collector")
    },
}

var del_clovisorCmd = &cobra.Command{
    Use:   "clovisor",
    Short: "Delete clovisor service from clovisor namespace",
    Long: ``,
    Run: func(cmd *cobra.Command, args []string) {
        fmt.Println("Deleting clovisor service")
        delCloverSystem("clovisor")
        cloverkube.ConfigNamespace("clovisor", "delete")
    },
}

var del_visibilityCmd = &cobra.Command{
    Use:   "visibility",
    Short: "Delete visibility services from clover-system namespace",
    Long: ``,
    Run: func(cmd *cobra.Command, args []string) {
        fmt.Println("Deleting visibility services")
        delCloverSystem("spark")
        delCloverSystem("controller")
        delCloverSystem("collector")
        delCloverSystem("cassandra")
        delCloverSystem("redis")
        cloverkube.ConfigNamespace("clover-system", "delete")
    },
}

var del_datastoreCmd = &cobra.Command{
    Use:   "datastore",
    Short: "Delete datastore services from clover-system namespace",
    Long: ``,
    Run: func(cmd *cobra.Command, args []string) {
        fmt.Println("Deleting datatore services")
        delCloverSystem("cassandra")
        delCloverSystem("redis")
    },
}

var del_validationCmd = &cobra.Command{
    Use:   "validation",
    Short: "Delete jmeter master/slave services",
    Long: ``,
    Run: func(cmd *cobra.Command, args []string) {
        fmt.Println("Deleting validation services")
        delCloverSystem("jmeter_master")
        delCloverSystem("jmeter_slave")
    },
}

func init() {
    deleteCmd.AddCommand(delsystemCmd)
    delsystemCmd.AddCommand(del_controllerCmd)
    del_controllerCmd.AddCommand(del_controllernodeportCmd)
    del_controllerCmd.AddCommand(del_controllerlbCmd)
    delsystemCmd.AddCommand(del_collectorCmd)
    delsystemCmd.AddCommand(del_visibilityCmd)
    delsystemCmd.AddCommand(del_validationCmd)
    delsystemCmd.AddCommand(del_datastoreCmd)
    delsystemCmd.AddCommand(del_clovisorCmd)
}

func delCloverSystem(clover_services string) {
    ns := "clover-system"
    switch clover_services {
        case "controller":
            cloverkube.DeleteResource("clover-controller", "deployment", ns)
            cloverkube.DeleteResource("clover-controller-internal",
                                      "service", ns)
        case "controller_nodeport", "controller_lb":
            cloverkube.DeleteResource("clover-controller",
                                      "service", ns)
        case "collector":
            cloverkube.DeleteResource("clover-collector", "deployment", ns)
            cloverkube.DeleteResource("clover-collector", "service", ns)
        case "spark":
            cloverkube.DeleteResource("clover-spark", "serviceaccount", ns)
            cloverkube.DeleteResource("clover-spark-default",
                                      "clusterrolebinding", ns)
            cloverkube.DeleteResource("clover-spark", "clusterrolebinding", ns)
            cloverkube.DeleteResource("clover-spark-submit", "deployment", ns)
        case "clovisor":
            cloverkube.DeleteResource("clovisor", "serviceaccount", "clovisor")
            cloverkube.DeleteResource("serv-account-rbac-clovisor",
                                      "clusterrolebinding", "clovisor")
            cloverkube.DeleteResource("clovisor", "daemonset", "clovisor")
        case "redis":
            cloverkube.DeleteResource("redis", "pod", ns)
            cloverkube.DeleteResource("redis", "service", ns)
        case "cassandra":
            cloverkube.DeleteResource("cassandra", "statefulset", ns)
            cloverkube.DeleteResource("cassandra", "service", ns)
        case "jmeter_master":
            cloverkube.DeleteResource("clover-jmeter-master", "deployment",
                                       "default")
            cloverkube.DeleteResource("clover-jmeter-master",
                                      "service", "default")
        case "jmeter_slave":
            cloverkube.DeleteResource("clover-jmeter-slave", "deployment",
                                       "default")
            cloverkube.DeleteResource("clover-jmeter-slave",
                                      "service", "default")
    }
}
