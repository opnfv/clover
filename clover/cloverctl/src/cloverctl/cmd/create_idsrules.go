// Copyright (c) Authors of Clover
//
// All rights reserved. This program and the accompanying materials
// are made available under the terms of the Apache License, Version 2.0
// which accompanies this distribution, and is available at
// http://www.apache.org/licenses/LICENSE-2.0

package cmd

import (
    "fmt"
    "io/ioutil"
    "gopkg.in/resty.v1"
    "github.com/ghodss/yaml"
    "github.com/spf13/cobra"
)


var idsrulesCmd = &cobra.Command{
    Use:   "idsrules",
    Short: "Create one or many IDS rules from yaml file",
    Long: ``,
    Run: func(cmd *cobra.Command, args []string) {
        createIDSRules()
    },
}

func init() {
    createCmd.AddCommand(idsrulesCmd)
    idsrulesCmd.Flags().StringVarP(&cloverFile, "file", "f", "", "Input yaml file to add IDS rules")
    idsrulesCmd.MarkFlagRequired("file")

}

func createIDSRules() {
    url := controllerIP + "/snort/addrule"
    in, err := ioutil.ReadFile(cloverFile)
    if err != nil {
        fmt.Println("Please specify a valid rule definition yaml file")
        return
    }
    out_json, err := yaml.YAMLToJSON(in)
    if err != nil {
        panic(err.Error())
    }
    resp, err := resty.R().
    SetHeader("Content-Type", "application/json").
    SetBody(out_json).
    Post(url)
    if err != nil {
        panic(err.Error())
    }
    fmt.Printf("\n%v\n", resp)
    //fmt.Println(string(out_json))

}
