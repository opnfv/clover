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

var JmeterResult string

var testresultCmd = &cobra.Command{
    Use:   "testresult",
    Short: "Get test results from L7 client emulation",
    Long: ``,
    Run: func(cmd *cobra.Command, args []string) {
        getResult()
    },
}

func init() {
    getCmd.AddCommand(testresultCmd)
    testresultCmd.Flags().StringVarP(&JmeterResult, "r", "r", "", "Result to retrieve - use 'log' or 'results'")
    testresultCmd.MarkFlagRequired("r")

}


func getResult() {
    switch JmeterResult {
        case "results":
            url := controllerIP + "/jmeter/results/results"
            resp, err := resty.R().
            Get(url)
            if err != nil {
                panic(err.Error())
            }
            fmt.Printf("\nResponse Body: %v\n", resp)
        case "log":
            url := controllerIP + "/jmeter/results/log"
            resp, err := resty.R().
            Get(url)
            if err != nil {
                panic(err.Error())
            }
            fmt.Printf("\nResponse Body: %v\n", resp)
        default:
            fmt.Println("Unrecoginized jmeter result type - use 'log' or 'results'")
       }
}
