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

var systemCmd = &cobra.Command{
    Use:   "system",
    Short: "Deploy clover-system services in Kubernetes",
    Long: ``,
    Run: func(cmd *cobra.Command, args []string) {
        cloverkube.ConfigNamespace("clover-system", "create")
    },
}

var create_visibilityCmd = &cobra.Command{
    Use:   "visibility",
    Short: "Deploy visibility services in clover-system namespace",
    Long: ``,
    Run: func(cmd *cobra.Command, args []string) {
        fmt.Println("Creating visibility services")
        cloverkube.ConfigNamespace("clover-system", "create")
        createCloverSystem("cassandra")
        createCloverSystem("redis")
        createCloverSystem("collector")
        createCloverSystem("controller")
        createCloverSystem("spark")
    },
}

var create_collectorCmd = &cobra.Command{
    Use:   "collector",
    Short: "Deploy collector service in clover-system namespace",
    Long: ``,
    Run: func(cmd *cobra.Command, args []string) {
        fmt.Println("Creating collector service")
        cloverkube.ConfigNamespace("clover-system", "create")
        createCloverSystem("collector")
    },
}

var create_controllerCmd = &cobra.Command{
    Use:   "controller",
    Short: "Deploy controller service in clover-system namespace",
    Long: ``,
    Run: func(cmd *cobra.Command, args []string) {
        fmt.Println("Creating controller service")
        cloverkube.ConfigNamespace("clover-system", "create")
        createCloverSystem("controller")
    },
}

var create_controllernodeportCmd = &cobra.Command{
    Use:   "nodeport",
    Short: "Deploy nodeport service to expose controller externally",
    Long: ``,
    Run: func(cmd *cobra.Command, args []string) {
        fmt.Println("Creating nodeport for controller service")
        createCloverSystem("controller_nodeport")
    },
}

var create_controllerlbCmd = &cobra.Command{
    Use:   "lb",
    Short: "Deploy lb service to expose controller externally",
    Long: ``,
    Run: func(cmd *cobra.Command, args []string) {
        fmt.Println("Creating lb for controller service")
        createCloverSystem("controller_lb")
    },
}

var create_clovisorCmd = &cobra.Command{
    Use:   "clovisor",
    Short: "Deploy clovisor service in clovisor namespace",
    Long: ``,
    Run: func(cmd *cobra.Command, args []string) {
        fmt.Println("Creating clovisor service")
        cloverkube.ConfigNamespace("clovisor", "create")
        createCloverSystem("clovisor")
    },
}

var create_datastoreCmd = &cobra.Command{
    Use:   "datastore",
    Short: "Deploy redis/cassandra services in clover-system namespace",
    Long: ``,
    Run: func(cmd *cobra.Command, args []string) {
        fmt.Println("Creating datastore services")
        cloverkube.ConfigNamespace("clover-system", "create")
        createCloverSystem("cassandra")
        createCloverSystem("redis")
    },
}

var create_validationCmd = &cobra.Command{
    Use:   "validation",
    Short: "Deploy jmeter master/slave services",
    Long: ``,
    Run: func(cmd *cobra.Command, args []string) {
        fmt.Println("Creating validation services")
        createCloverSystem("jmeter_master")
        createCloverSystem("jmeter_slave")
    },
}


var repo string
var tag string
func init() {
    createCmd.AddCommand(systemCmd)
    systemCmd.AddCommand(create_visibilityCmd)
    systemCmd.AddCommand(create_collectorCmd)
    systemCmd.AddCommand(create_controllerCmd)
    create_controllerCmd.AddCommand(create_controllernodeportCmd)
    create_controllerCmd.AddCommand(create_controllerlbCmd)
    systemCmd.AddCommand(create_datastoreCmd)
    systemCmd.AddCommand(create_validationCmd)
    systemCmd.AddCommand(create_clovisorCmd)
    systemCmd.PersistentFlags().StringVarP(&repo, "repo", "r", "opnfv",
                         "Image repo to use, ex.  'opnfv' or 'localhost:5000'")
    systemCmd.PersistentFlags().StringVarP(&tag, "tag", "t", "opnfv-7.0.0",
                             "Image tag to use, ex. 'opnfv-7.0.0' or 'latest'")
}

func createCloverSystem(clover_services string) {
    image := ""
    switch clover_services {
        case "controller":
            image = repo + "/clover-controller:" + tag
            cloverkube.CreateResource("controller/deployment.yaml",
                                      "deployment", image, "")
            cloverkube.CreateResource("controller/service_internal.yaml",
                                      "service", "", "")
        case "controller_nodeport":
            cloverkube.CreateResource("controller/service_nodeport.yaml",
                                      "service", "", "")
        case "controller_lb":
            cloverkube.CreateResource("controller/service_lb.yaml",
                                      "service", "", "")
        case "collector":
            image = repo + "/clover-collector:" + tag
            cloverkube.CreateResource("collector/deployment.yaml",
                                      "deployment", image, "")
            cloverkube.CreateResource("collector/service.yaml", "service",
                                       "", "")
        case "spark":
            image = repo + "/clover-spark-submit:" + tag
            cloverkube.CreateResource("spark/serviceaccount.yaml",
                                      "serviceaccount", "", "")
            cloverkube.CreateResource("spark/clusterrolebinding.yaml",
                                      "clusterrolebinding", "", "")
            cloverkube.CreateResource("spark/clusterrolebinding_spark.yaml",
                                      "clusterrolebinding", "", "")
            cloverkube.CreateResource("spark/deployment.yaml", "deployment",
                                      image, "")
         case "clovisor":
            image = repo + "/clover-clovisor:" + tag
            cloverkube.CreateResource("clovisor/serviceaccount.yaml",
                                      "serviceaccount", "", "clovisor")
            cloverkube.CreateResource("clovisor/clusterrolebinding.yaml",
                                      "clusterrolebinding", "", "clovisor")
            cloverkube.CreateResource("clovisor/daemonset.yaml", "daemonset",
                                      image, "clovisor")
        case "redis":
            cloverkube.CreateResource("datastore/redis_pod.yaml", "pod",
                                       "", "")
            cloverkube.CreateResource("datastore/redis_service.yaml",
                                      "service", "", "")
        case "cassandra":
            cloverkube.CreateResource("datastore/cassandra_statefulset.yaml",
                                      "statefulset", "", "")
            cloverkube.CreateResource("datastore/cassandra_service.yaml",
                                      "service", "", "")
        case "jmeter_master":
            image = repo + "/clover-jmeter-master:" + tag
            cloverkube.CreateResource("jmeter/master_deployment.yaml",
                                      "deployment", image, "default")
            cloverkube.CreateResource("jmeter/master_service.yaml",
                                      "service", "", "default")
        case "jmeter_slave":
            image = repo + "/clover-jmeter-slave:" + tag
            cloverkube.CreateResource("jmeter/slave_deployment.yaml",
                                      "deployment", image, "default")
            cloverkube.CreateResource("jmeter/slave_service.yaml",
                                      "service", "", "default")
    }
}
