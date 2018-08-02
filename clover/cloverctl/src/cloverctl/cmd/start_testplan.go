// Copyright (c) Authors of Clover
//
// All rights reserved. This program and the accompanying materials
// are made available under the terms of the Apache License, Version 2.0
// which accompanies this distribution, and is available at
// http://www.apache.org/licenses/LICENSE-2.0

package cmd

import (
    "fmt"
    "strings"
    "gopkg.in/resty.v1"
    "github.com/spf13/cobra"
    "cloverkube"
)


var testplanstartCmd = &cobra.Command{
    Use:   "testplan",
    Short: "Start a test for a given test plan",
    Long: `Specify number of slaves to use with '-s' flag. Default is 0 slaves,
which runs tests only from jmeter-master.`,
    Run: func(cmd *cobra.Command, args []string) {
        startTest()
        //fmt.Printf("%v\n", cmd.Parent().CommandPath())
    },
}
var num_slaves int

func init() {
    startCmd.AddCommand(testplanstartCmd)
    testplanstartCmd.PersistentFlags().StringVarP(&cloverFile, "file", "f", "", "Currently unused")
    testplanstartCmd.PersistentFlags().IntVarP(&num_slaves, "slaves", "s", 0, "Number of slaves to use")
}

func startTest() {

    ips := cloverkube.GetPodsIP("clover-jmeter-slave", "default")
    fmt.Printf("\njmeter-slaves found: %s\n", ips)
    if num_slaves > len(ips) {
        fmt.Printf("Number of slaves specified must be less than found: %d\n", len(ips))
        return
    }
    ip_list := strings.Join(ips[0:num_slaves], ",")

    url := controllerIP + "/jmeter/start"
    resp, err := resty.R().
    SetHeader("Content-Type", "application/json").
    SetBody(fmt.Sprintf(`{"num_slaves":"%d", "slave_list":"%s"}`, num_slaves, ip_list)).
    Post(url)
    if err != nil {
        panic(err.Error())
    }
    fmt.Printf("\n%v\n", resp)

}


