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
    "gopkg.in/resty.v1"
    "io/ioutil"
    "github.com/ghodss/yaml"
    "github.com/spf13/cobra"

)


var testplanCmd = &cobra.Command{
    Use:   "testplan",
    Short: "Create jmeter L7 client emulation test plan from yaml file",
    Long: ``,
    Run: func(cmd *cobra.Command, args []string) {
        createTestPlan()
    },
}

func init() {
    createCmd.AddCommand(testplanCmd)
    testplanCmd.Flags().StringVarP(&cloverFile, "file", "f", "",
                                   "Input test plan yaml file")
    testplanCmd.MarkFlagRequired("file")
}

func createTestPlan() {
    checkControllerIP()
    url := controllerIP + "/jmeter/gen"
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
