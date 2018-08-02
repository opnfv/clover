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


var visibilitystopCmd = &cobra.Command{
    Use:   "visibility",
    Short: "Stop visibility data collection",
    Long: ``,
    Run: func(cmd *cobra.Command, args []string) {
        stopCollector()
    },
}

func init() {
    stopCmd.AddCommand(visibilitystopCmd)
}

func stopCollector() {

    url := controllerIP + "/collector/stop"

    resp, err := resty.R().
    Get(url)
    if err != nil {
        panic(err.Error())
    }
    fmt.Printf("\n%v\n", resp)
}


