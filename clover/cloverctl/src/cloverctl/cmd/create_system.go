// Copyright (c) Authors of Clover
//
// All rights reserved. This program and the accompanying materials
// are made available under the terms of the Apache License, Version 2.0
// which accompanies this distribution, and is available at
// http://www.apache.org/licenses/LICENSE-2.0

package cmd

import (
    "fmt"
    //"io/ioutil"
    //"github.com/ghodss/yaml"
    "github.com/spf13/cobra"
    "cloverkube"
)


var systemCmd = &cobra.Command{
    Use:   "system",
    Short: "Deploy clover-system in Kubernetes",
    Long: ``,
    Run: func(cmd *cobra.Command, args []string) {
        createCloverSystem()
    },
}

func init() {
    createCmd.AddCommand(systemCmd)
    //systemCmd.PersistentFlags().StringVarP(&cloverFile, "f", "f", "", "Input yaml file to create system")

}

func createCloverSystem() {
    cloverkube.DeployCloverSystem("create", "clover-system")
    fmt.Println("Deployed clover-system successfully")
}
