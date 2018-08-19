// Copyright (c) Authors of Clover
//
// All rights reserved. This program and the accompanying materials
// are made available under the terms of the Apache License, Version 2.0
// which accompanies this distribution, and is available at
// http://www.apache.org/licenses/LICENSE-2.0

package cloverinject

import (
   "io"
   "os"
   "fmt"
   metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
   "istio.io/istio/pilot/pkg/kube/inject"
   meshconfig "istio.io/api/mesh/v1alpha1"
   "k8s.io/client-go/kubernetes"
   "istio.io/istio/pkg/kube"
   "istio.io/istio/pilot/pkg/model"
   "github.com/ghodss/yaml"
   "istio.io/istio/pilot/cmd"

)
//var _ = inject.InitImageName

func CloverInject(inFilename string) {

    var err error
    var kubeconfig string

    var reader io.Reader


    var in *os.File
    in, err = os.Open(inFilename)
    if err != nil {
        panic(err.Error())
    }
    reader = in

    var writer io.Writer
    outFilename := "out_sdc.yaml"
    var out *os.File
    out, err = os.Create(outFilename)
    writer = out

    var sidecarTemplate string
    if sidecarTemplate, err = getInjectConfigFromConfigMap(kubeconfig); err != nil {
        fmt.Printf("this is a template gen error")
        panic(err.Error())
    }

    var meshConfig *meshconfig.MeshConfig
    meshConfigFile := "mesh-config.yaml"
    if meshConfig, err = cmd.ReadMeshConfig(meshConfigFile); err != nil {
        panic(err.Error())
    }

    inject.IntoResourceFile(sidecarTemplate, meshConfig, reader, writer)

}

func getMeshConfigFromConfigMap(kubeconfig string) (*meshconfig.MeshConfig, error) {
    client, err := createInterface(kubeconfig)
    if err != nil {
        return nil, err
    }

    istioNamespace := "istio-system"
    meshConfigMapName := "istio"
    configMapKey := "mesh"

    config, err := client.CoreV1().ConfigMaps(istioNamespace).Get(meshConfigMapName, metav1.GetOptions{})
    if err != nil {
        return nil, fmt.Errorf("could not read valid configmap %q from namespace  %q: %v - "+
            "Use --meshConfigFile or re-run kube-inject with `-i <istioSystemNamespace> and ensure valid MeshConfig exists",
            meshConfigMapName, istioNamespace, err)
    }
    // values in the data are strings, while proto might use a
    // different data type.  therefore, we have to get a value by a
    // key
    configYaml, exists := config.Data[configMapKey]
    if !exists {
        return nil, fmt.Errorf("missing configuration map key %q", configMapKey)
    }
    return model.ApplyMeshConfigDefaults(configYaml)
}

func getInjectConfigFromConfigMap(kubeconfig string) (string, error) {
    client, err := createInterface(kubeconfig)
    if err != nil {
        return "", err
    }
    // added by me
    istioNamespace := "istio-system"
    injectConfigMapName := "istio-inject"
    //injectConfigMapName := "istio-sidecar-injector"
    injectConfigMapKey := "config"


    config, err := client.CoreV1().ConfigMaps(istioNamespace).Get(injectConfigMapName, metav1.GetOptions{})
    if err != nil {
        return "", fmt.Errorf("could not find valid configmap %q from namespace  %q: %v - "+
            "Use --injectConfigFile or re-run kube-inject with `-i <istioSystemNamespace> and ensure istio-inject configmap exists",
            injectConfigMapName, istioNamespace, err)
    }
    // values in the data are strings, while proto might use a
    // different data type.  therefore, we have to get a value by a
    // key
    injectData, exists := config.Data[injectConfigMapKey]
    if !exists {
        return "", fmt.Errorf("missing configuration map key %q in %q",
            injectConfigMapKey, injectConfigMapName)
    }
    var injectConfig inject.Config
    if err := yaml.Unmarshal([]byte(injectData), &injectConfig); err != nil {
        return "", fmt.Errorf("unable to convert data from configmap %q: %v",
            injectConfigMapName, err)
    }
    //log.Debugf("using inject template from configmap %q", injectConfigMapName)
    return injectConfig.Template, nil
}


func homeDir() string {
    if h := os.Getenv("HOME"); h != "" {
        return h
    }
    return os.Getenv("USERPROFILE") // windows
}

func createInterface(kubeconfig string) (kubernetes.Interface, error) {

    var configContext string
    restConfig, err := kube.BuildClientConfig(kubeconfig, configContext)

    if err != nil {
        return nil, err
    }
    return kubernetes.NewForConfig(restConfig)
}
