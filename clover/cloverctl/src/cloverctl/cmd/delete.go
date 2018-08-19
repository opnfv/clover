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

var deleteCmd = &cobra.Command{
    Use:   "delete",
    Short: "Delete resources including clover-system services",
    Long: ``,
    Run: func(cmd *cobra.Command, args []string) {
        fmt.Println("delete called")
    },
}

func init() {
    rootCmd.AddCommand(deleteCmd)
}
