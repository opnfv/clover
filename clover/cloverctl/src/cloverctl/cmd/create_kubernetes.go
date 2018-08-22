// Copyright (c) Authors of Clover
//
// All rights reserved. This program and the accompanying materials
// are made available under the terms of the Apache License, Version 2.0
// which accompanies this distribution, and is available at
// http://www.apache.org/licenses/LICENSE-2.0

package cmd

import (
    "fmt"
    "time"
    "io/ioutil"
    "strings"

    "gopkg.in/resty.v1"
    "github.com/ghodss/yaml"
    "github.com/spf13/cobra"
    "cloverkube"
)

type Kubernetes struct {
    Name        string
    ProviderVersion string
    KubeconfigFile string
    DockerRegistries []DockerRegistry
}

type DockerRegistry struct {
    AccountName string
}


var kubeproviderCmd = &cobra.Command{
    Use:   "kubernetes",
    Short: "Add one kubernete provider from yaml file to spinnaker",
    Long: ``,
    Run: func(cmd *cobra.Command, args []string) {
        createProvider()
    },
}

func init() {
    providercreateCmd.AddCommand(kubeproviderCmd)
    kubeproviderCmd.Flags().StringVarP(&cloverFile, "file", "f", "", "Input yaml file to add kubernetes provider")
    kubeproviderCmd.MarkFlagRequired("file")

}

func createProvider() {
    url := controllerIP + "/halyard/addkube"
    in, err := ioutil.ReadFile(cloverFile)
    if err != nil {
        fmt.Println("Please specify a valid rule definition yaml file")
        return
    }

    t := Kubernetes{}
    yaml.Unmarshal(in, &t)
    if(t.KubeconfigFile==""){
        fmt.Println("error")
        return;
    }
    filename := t.KubeconfigFile
    hal_path := "/home/spinnaker/config"
    timestamp := time.Now().Unix()
    tm := time.Unix(timestamp, 0)
    t.KubeconfigFile = hal_path + tm.Format("2006-01-02-15-04-05")
    dest_container := "spinnaker/spin-halyard/halyard-daemon"
    destPath := t.KubeconfigFile
    dest := strings.Join([]string{dest_container, destPath}, ":")
    cloverkube.CopyFileToPod(filename, dest)
    newconfig, _ := yaml.Marshal(&t)
    out_json, err := yaml.YAMLToJSON(newconfig)
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

}
