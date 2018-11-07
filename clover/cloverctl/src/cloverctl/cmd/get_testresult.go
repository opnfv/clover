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
    "github.com/spf13/cobra"
)

var testresultCmd = &cobra.Command{
    Use:   "testresult",
    Short: "Get test results from jmeter L7 client emulation",
    Long: ``,
    Run: func(cmd *cobra.Command, args []string) {
        getResult("log")
    },
}

var log_testresultCmd = &cobra.Command{
    Use:   "log",
    Short: "Get jmeter summary log results",
    Long: ``,
    Run: func(cmd *cobra.Command, args []string) {
        getResult("log")
    },
}

var detail_testresultCmd = &cobra.Command{
    Use:   "detail",
    Short: "Get jmeter detailed results",
    Long: ``,
    Run: func(cmd *cobra.Command, args []string) {
        getResult("detail")
    },
}

func init() {
    getCmd.AddCommand(testresultCmd)
    testresultCmd.AddCommand(log_testresultCmd)
    testresultCmd.AddCommand(detail_testresultCmd)
}

func getResult(result_type string) {
    checkControllerIP()
    switch result_type {
        case "detail":
            url := controllerIP + "/jmeter/results/results"
            resp, err := resty.R().
            Get(url)
            if err != nil {
                fmt.Printf("Cannot connect to controller: %v\n", err)
                os.Exit(1)
            }
            fmt.Printf("\nResponse Body: %v\n", resp)
        case "log":
            url := controllerIP + "/jmeter/results/log"
            resp, err := resty.R().
            Get(url)
            if err != nil {
                fmt.Printf("Cannot connect to controller: %v\n", err)
                os.Exit(1)
            }
            fmt.Printf("\nResponse Body: %v\n", resp)
        default:
            msg := "Unrecoginized jmeter result type"
            fmt.Printf("%s - use 'log' or 'detail'", msg)
       }
}
