// Copyright (c) Authors of Clover
//
// All rights reserved. This program and the accompanying materials
// are made available under the terms of the Apache License, Version 2.0
// which accompanies this distribution, and is available at
// http://www.apache.org/licenses/LICENSE-2.0

package cmd

import (
    "fmt"
    "gopkg.in/resty.v1"
    "github.com/spf13/cobra"
)

var VisibilityStat string
var VisibilityConfig string

var visibilitygetCmd = &cobra.Command{
    Use:   "visibility",
    Short: "Get visibility config & stats",
    Long: ``,
    Run: func(cmd *cobra.Command, args []string) {
        getVisibility()
    },
}

func init() {
    getCmd.AddCommand(visibilitygetCmd)
    visibilitygetCmd.PersistentFlags().StringVarP(&VisibilityStat, "stat", "s", "", "Visibility stats type to get")
    visibilitygetCmd.PersistentFlags().StringVarP(&VisibilityConfig, "conf", "c", "", "Visibility config type to get")
}

func getVisibility() {

    url_prefix := "/visibility/get/"
    get_data := "all"
    response_prefix := "Config"
    if VisibilityStat != "" {
        url_prefix = "/visibility/get/stats/"
        get_data =  VisibilityStat
        response_prefix = "Stat"
    } else if VisibilityConfig != "" {
        get_data =  VisibilityConfig
    }

    url := controllerIP + url_prefix + get_data

    resp, err := resty.R().
    SetHeader("Accept", "application/json").
    Get(url)
    if err != nil {
        panic(err.Error())
    }
    fmt.Printf("\n%s %s: %v\n", response_prefix, get_data, resp)
}
