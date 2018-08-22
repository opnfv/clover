// Copyright (c) Authors of Clover
//
// All rights reserved. This program and the accompanying materials
// are made available under the terms of the Apache License, Version 2.0
// which accompanies this distribution, and is available at
// http://www.apache.org/licenses/LICENSE-2.0

package cmd

import (
    "fmt"
    "github.com/spf13/cobra"
)

var providercreateCmd = &cobra.Command{
    Use:   "provider",
    Short: "Add spinnaker provider",
    Long: ``,
    Run: func(cmd *cobra.Command, args []string) {
        fmt.Println("provider called")
    },
}

var providerdelCmd = &cobra.Command{
    Use:   "provider",
    Short: "Delete spinnaker provider",
    Long: ``,
    Run: func(cmd *cobra.Command, args []string) {
        fmt.Println("provider called")
    },
}

var providergetCmd = &cobra.Command{
    Use:   "provider",
    Short: "Get spinnaker provider",
    Long: ``,
    Run: func(cmd *cobra.Command, args []string) {
        fmt.Println("provider called")
    },
}
func init() {
    createCmd.AddCommand(providercreateCmd)
    deleteCmd.AddCommand(providerdelCmd)
    getCmd.AddCommand(providergetCmd)
}
