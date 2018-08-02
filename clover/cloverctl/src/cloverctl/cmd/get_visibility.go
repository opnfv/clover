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


var visibilitystatsCmd = &cobra.Command{
    Use:   "visibility",
    Short: "Get toplevel visibility stats",
    Long: ``,
    Run: func(cmd *cobra.Command, args []string) {
        statsCollector()
    },
}

func init() {
    getCmd.AddCommand(visibilitystatsCmd)
    //visibilitystartCmd.PersistentFlags().StringVarP(&cloverFile, "f", "f", "", "Input yaml file with test plan params")
}

func statsCollector() {
    url := controllerIP + "/collector/stats"

    resp, err := resty.R().
    SetHeader("Accept", "application/json").
    Get(url)
    if err != nil {
        panic(err.Error())
    }
    fmt.Printf("\nProxy Response Time: %v\n", resp)
}
