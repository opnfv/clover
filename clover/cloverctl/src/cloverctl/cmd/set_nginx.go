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
    "github.com/spf13/cobra"
    "github.com/ghodss/yaml"
)


var setserverCmd = &cobra.Command{
    Use:   "server",
    Short: "Modify nginx server configuration",
    Long: ``,
    Run: func(cmd *cobra.Command, args []string) {
        setNginx("server")
    },
}

var setlbCmd = &cobra.Command{
    Use:   "lb",
    Short: "Modify nginx lb configuration",
    Long: ``,
    Run: func(cmd *cobra.Command, args []string) {
        setNginx("lb")
    },
}

func init() {
    setCmd.AddCommand(setserverCmd)
    setserverCmd.Flags().StringVarP(&cloverFile, "file", "f", "",
                                    "Input yaml file for server config")
    setserverCmd.MarkFlagRequired("file")

    setCmd.AddCommand(setlbCmd)
    setlbCmd.Flags().StringVarP(&cloverFile, "file", "f", "",
                                "Input yaml file for lb config")
    setlbCmd.MarkFlagRequired("file")
}

func setNginx(nginx_service string) {

    checkControllerIP()
    url := ""
    if nginx_service == "server" {
        url = controllerIP + "/nginx/server"
    } else {
        url = controllerIP + "/nginx/lb"
    }

    in, err := ioutil.ReadFile(cloverFile)
    if err != nil {
        fmt.Println("Please specify a valid yaml file")
        os.Exit(1)
    }
    out_json, err := yaml.YAMLToJSON(in)
    if err != nil {
        fmt.Printf("Invalid yaml: %v\n", err)
        os.Exit(1)
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
