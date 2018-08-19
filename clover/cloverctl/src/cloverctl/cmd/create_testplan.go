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
    "io/ioutil"
    "github.com/ghodss/yaml"
    "github.com/spf13/cobra"
)


var testplanCmd = &cobra.Command{
    Use:   "testplan",
    Short: "Create L7 client emulation test plans from yaml file",
    Long: ``,
    Run: func(cmd *cobra.Command, args []string) {
        createTestPlan()
        //fmt.Printf("%v\n", cmd.Parent().CommandPath())
    },
}

func init() {
    createCmd.AddCommand(testplanCmd)
    testplanCmd.Flags().StringVarP(&cloverFile, "file", "f", "", "Input yaml file with test plan params")
    testplanCmd.MarkFlagRequired("file")
}

func createTestPlan() {
    url := controllerIP + "/jmeter/gen"
    in, err := ioutil.ReadFile(cloverFile)
    if err != nil {
        fmt.Println("Please specify a valid test plan yaml file")
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

