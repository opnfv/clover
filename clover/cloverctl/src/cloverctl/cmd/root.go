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

    homedir "github.com/mitchellh/go-homedir"
    "github.com/spf13/cobra"
    "github.com/spf13/viper"
    "cloverkube"
)

var cfgFile string

var controllerIP string
var cloverFile string

// rootCmd represents the base command when called without any subcommands
var rootCmd = &cobra.Command{
    Use:   "cloverctl",
    Short: "Command-Line Interface (CLI) for Clover",
    Long: ``,
    // Uncomment the following line if your bare application
    // has an action associated with it:
    //Run: func(cmd *cobra.Command, args []string) {
    //},
}

// Execute adds all child commands to the root command and sets flags appropriately.
// This is called by main.main(). It only needs to happen once to the rootCmd.
func Execute() {
    if err := rootCmd.Execute(); err != nil {
        fmt.Println(err)
        os.Exit(1)
    }
}

func init() {
    cobra.OnInitialize(initConfig)

    // Here you will define your flags and configuration settings.
    // Cobra supports persistent flags, which, if defined here,
    // will be global for your application.
    rootCmd.PersistentFlags().StringVar(&cfgFile, "config", "", "config file (default is $HOME/.cloverctl.yaml)")

    // Cobra also supports local flags, which will only run
    // when this action is called directly.
    rootCmd.Flags().BoolP("toggle", "t", false, "Help message for toggle")

    cPort, cIP := cloverkube.GetServicesPortIP("clover-controller")
    if cIP == "" {
        controllerIP = "http://10.244.0.1:" + fmt.Sprint(cPort)
    } else {
        controllerIP = "http://" + cIP
    }
    fmt.Printf("\nclover-controller: %s %s\n", fmt.Sprint(cPort), cIP)
}

// initConfig reads in config file and ENV variables if set.
func initConfig() {
    if cfgFile != "" {
    // Use config file from the flag.
        viper.SetConfigFile(cfgFile)
    } else {
    // Find home directory.
        home, err := homedir.Dir()
        if err != nil {
            fmt.Println(err)
            os.Exit(1)
        }

        // Search config in home directory with name ".cloverctl" (without extension).
        viper.AddConfigPath(home)
        viper.SetConfigName(".cloverctl")
    }

    viper.AutomaticEnv() // read in environment variables that match

    // If a config file is found, read it in.
    if err := viper.ReadInConfig(); err == nil {
        fmt.Println("Using config file:", viper.ConfigFileUsed())
    }
}
