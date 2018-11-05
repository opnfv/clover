// Copyright (c) Authors of Clover
//
// All rights reserved. This program and the accompanying materials
// are made available under the terms of the Apache License, Version 2.0
// which accompanies this distribution, and is available at
// http://www.apache.org/licenses/LICENSE-2.0

package cmd

import (
    "fmt"
    "os"
    "io/ioutil"
    "gopkg.in/resty.v1"
    "github.com/ghodss/yaml"
    "github.com/spf13/cobra"
)


var visibilitystartCmd = &cobra.Command{
    Use:   "visibility",
    Short: "Start visibility collector process",
    Long: ``,
    Run: func(cmd *cobra.Command, args []string) {
        startCollector()
    },
}

func init() {
    startCmd.AddCommand(visibilitystartCmd)
    visibilitystartCmd.PersistentFlags().StringVarP(&cloverFile, "file", "f", "", "Optional yaml file with collector params")
}

func startCollector() {

    var message_body string
    if cloverFile != "" {
        in, err := ioutil.ReadFile(cloverFile)
        if err != nil {
            fmt.Printf("Cannot read file: %v\n", err)
            os.Exit(1)
        }
        out_json, err := yaml.YAMLToJSON(in)
        message_body = string(out_json)
        if err != nil {
            fmt.Printf("Invalid yaml: %v\n", err)
            os.Exit(1)
        }
    } else {
        message_body = `{"sample_interval":"10", "t_port":"80", "t_host":"jaeger-query.istio-system"}`
    }
    checkControllerIP()
    url := controllerIP + "/collector/start"
    resp, err := resty.R().
    SetHeader("Content-Type", "application/json").
    SetBody(message_body).
    Post(url)
    if err != nil {
        fmt.Printf("Cannot connect to controller: %v\n", err)
        os.Exit(1)
    }
    fmt.Printf("\n%v\n", resp)
}


