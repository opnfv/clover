// Copyright (c) Authors of Clover
//
// All rights reserved. This program and the accompanying materials
// are made available under the terms of the Apache License, Version 2.0
// which accompanies this distribution, and is available at
// http://www.apache.org/licenses/LICENSE-2.0

package cmd

import (
    "fmt"
    "encoding/json"
    "os"
    "gopkg.in/resty.v1"
    "github.com/spf13/cobra"
)

var deldockerproviderCmd = &cobra.Command{
    Use:   "docker-registry",
    Short: "Delete one docker registry provider by name from spinnaker",
    Long: ``,
    Run: func(cmd *cobra.Command, args []string) {
        deldockerProvider()
    },
}

func init() {
    providerdelCmd.AddCommand(deldockerproviderCmd)
    deldockerproviderCmd.Flags().StringVarP(&name, "name", "n", "",
                                          "Input docker-registry account name")
    deldockerproviderCmd.MarkFlagRequired("name")

}

func deldockerProvider() {
    checkControllerIP()
    url := controllerIP + "/halyard/delprovider"

    var in = map[string]string{"name": name, "provider":"dockerRegistry"}
    out_json, err := json.Marshal(in)
    if err != nil {
        fmt.Println("json.Marshal failed:", err)
        return
    }
    resp, err := resty.R().
    SetHeader("Content-Type", "application/json").
    SetBody(out_json).
    Post(url)
    if err != nil {
        fmt.Printf("Cannot connect to controller: %v\n", err)
        os.Exit(1)
    }
    fmt.Printf("\n%v\n", resp)

}
