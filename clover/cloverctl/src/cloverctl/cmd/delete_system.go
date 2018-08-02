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
    "cloverkube"
)


var delsystemCmd = &cobra.Command{
    Use:   "system",
    Short: "Delete clover-system in Kubernetes",
    Long: ``,
    Run: func(cmd *cobra.Command, args []string) {
        delCloverSystem()
    },
}

func init() {
    deleteCmd.AddCommand(delsystemCmd)
}

func delCloverSystem() {
    cloverkube.DeployCloverSystem("delete", "clover-system")
    fmt.Println("Deleted clover-system successfully")
}
