// Copyright (c) Authors of Clover
//
// All rights reserved. This program and the accompanying materials
// are made available under the terms of the Apache License, Version 2.0
// which accompanies this distribution, and is available at
// http://www.apache.org/licenses/LICENSE-2.0

package cmd

import (
    "fmt"
    "strings"
    "encoding/json"

    "gopkg.in/resty.v1"
    "github.com/spf13/cobra"
)


var getkubeprovider = &cobra.Command{
    Use:   "kubernetes",
    Short: "Get kubernetes provider from spinnaker",
    Long: ``,
    Run: func(cmd *cobra.Command, args []string) {
        getkube()
    },
}

func init() {
    providergetCmd.AddCommand(getkubeprovider)
}

func getkube() {
    url := controllerIP + "/halyard/account"

    var provider = map[string]string{"name": "kubernetes"}
    out_json, err := json.Marshal(provider)
    if err != nil {
        fmt.Println("json.Marshal failed:", err)
        return
    }
    resp, err := resty.SetAllowGetMethodPayload(true).R().
    SetHeader("Content-Type", "application/json").
    SetBody(out_json).
    Get(url)
    if err != nil {
        panic(err.Error())
    }
    if resp.StatusCode() != 200 {
       fmt.Printf("\n%v\n", resp)
       return
    }

    accounts := strings.Split(resp.String(), ":")
    fmt.Printf("\n")
    for index, account := range accounts{
        fmt.Printf("%d. %v\n",index + 1, account)
    }
}
