// Copyright (c) Authors of Clover
//
// All rights reserved. This program and the accompanying materials
// are made available under the terms of the Apache License, Version 2.0
// which accompanies this distribution, and is available at
// http://www.apache.org/licenses/LICENSE-2.0

package cloverkube

import (
    "fmt"
    "os"
    "path/filepath"
    "strings"
    "io/ioutil"
    "io"
    "bytes"

    appsv1 "k8s.io/api/apps/v1"
    apiv1 "k8s.io/api/core/v1"
    metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
    "k8s.io/client-go/kubernetes"
    "k8s.io/client-go/tools/clientcmd"
    "k8s.io/apimachinery/pkg/runtime"
    "k8s.io/client-go/tools/remotecommand"

)

func setClient() kubernetes.Interface {


    kubeconfig := filepath.Join(
         os.Getenv("HOME"), ".kube", "config",
    )
    config, err := clientcmd.BuildConfigFromFlags("", kubeconfig)
    if err != nil {
        panic(err.Error())
    }

    // create the clientset
    clientset, err := kubernetes.NewForConfig(config)
    if err != nil {
        panic(err.Error())
    }
    return clientset
}

func setControllerDeploy () (*appsv1.Deployment, *apiv1.Service) {

    deployment := &appsv1.Deployment{
        ObjectMeta: metav1.ObjectMeta{
            Name: "clover-controller",
        },
        Spec: appsv1.DeploymentSpec{
            Selector: &metav1.LabelSelector{
                MatchLabels: map[string]string{
                    "app": "clover-controller",
                },
            },
            Template: apiv1.PodTemplateSpec{
                ObjectMeta: metav1.ObjectMeta{
                    Labels: map[string]string{
                        "app": "clover-controller",
                    },
                },
                Spec: apiv1.PodSpec{
                    Containers: []apiv1.Container{
                        {
                            Name:  "clover-controller",
                            Image: "localhost:5000/clover-controller:latest",
                            Ports: []apiv1.ContainerPort{
                                {
                                    Name:          "redis",
                                    Protocol:      apiv1.ProtocolTCP,
                                    ContainerPort: 6379,
                                },
                                {
                                    Name:          "grpc",
                                    Protocol:      apiv1.ProtocolTCP,
                                    ContainerPort: 50054,
                                },
                                {
                                    Name:          "gprcsecurity",
                                    Protocol:      apiv1.ProtocolTCP,
                                    ContainerPort: 50052,
                                },
                                {
                                    Name:          "cassandra",
                                    Protocol:      apiv1.ProtocolTCP,
                                    ContainerPort: 9042,
                                },


                            },
                        },
                    },
                },
            },
        },
    }

    service := &apiv1.Service{
        ObjectMeta: metav1.ObjectMeta{
            Name: "clover-controller",
            Labels: map[string]string{
                "app": "clover-controller",
            },

        },
        Spec: apiv1.ServiceSpec{
            Selector: map[string]string{
                    "app": "clover-controller",
            },
            Type: "NodePort",
            Ports: []apiv1.ServicePort{
                {
                    Name: "http",
                    Port: 80,
                    NodePort: 32044,
                    Protocol: "TCP",
                },
            },
        },
    }

    return deployment, service

}

func setCollectorDeploy () (*appsv1.Deployment, *apiv1.Service) {

    deployment := &appsv1.Deployment{
        ObjectMeta: metav1.ObjectMeta{
            Name: "clover-collector",
        },
        Spec: appsv1.DeploymentSpec{
            Selector: &metav1.LabelSelector{
                MatchLabels: map[string]string{
                    "app": "clover-collector",
                },
            },
            Template: apiv1.PodTemplateSpec{
                ObjectMeta: metav1.ObjectMeta{
                    Labels: map[string]string{
                        "app": "clover-collector",
                    },
                },
                Spec: apiv1.PodSpec{
                    Containers: []apiv1.Container{
                        {
                            Name:  "clover-collector",
                            Image: "localhost:5000/clover-collector:latest",
                            Ports: []apiv1.ContainerPort{
                                {
                                    Name:          "redis",
                                    Protocol:      apiv1.ProtocolTCP,
                                    ContainerPort: 6379,
                                },
                                {
                                    Name:          "grpc",
                                    Protocol:      apiv1.ProtocolTCP,
                                    ContainerPort: 50054,
                                },
                                {
                                    Name:          "prometheus",
                                    Protocol:      apiv1.ProtocolTCP,
                                    ContainerPort: 9090,
                                },
                                {
                                    Name:          "jaeger",
                                    Protocol:      apiv1.ProtocolTCP,
                                    ContainerPort: 16686,
                                },
                                {
                                    Name:          "cassandra",
                                    Protocol:      apiv1.ProtocolTCP,
                                    ContainerPort: 9042,
                                },


                            },
                        },
                    },
                },
            },
        },
    }

    service := &apiv1.Service{
        ObjectMeta: metav1.ObjectMeta{
            Name: "clover-collector",
            Labels: map[string]string{
                "app": "clover-collector",
            },

        },
        Spec: apiv1.ServiceSpec{
            Selector: map[string]string{
                    "app": "clover-collector",
            },
            Ports: []apiv1.ServicePort{
                {
                    Name: "grpc",
                    Port: 50054,
                },
                {
                    Name: "redis",
                    Port: 6379,
                },
                {
                    Name: "prometheus",
                    Port: 9090,
                },
                {
                    Name: "jaeger",
                    Port: 16686,
                },
                {
                    Name: "cassandra",
                    Port: 9042,
                },

            },
        },
    }
    return deployment, service
}

func DeployCloverSystem(action string, namespace string) {
    if action == "create" {
        // Create clover-system namespace
        configNamespace("clover-system", "create")
        // Controller
        deployment, service := setControllerDeploy()
        DeployService(deployment, service, namespace)
        // Collector
        deployment, service = setCollectorDeploy()
        DeployService(deployment, service, namespace)
    } else if action  == "delete" {
        fmt.Println("Deleting clover-system services...\n")
        DeleteService("clover-controller", namespace)
        DeleteService("clover-collector", namespace)
        configNamespace("clover-system", "delete")
    }

}

func DeleteService(deploy_name string, namespace string) {

    clientset := setClient()
    deploymentsClient := clientset.AppsV1().Deployments(namespace)
    servicesClient := clientset.CoreV1().Services(namespace)

    // Delete Deployment
    deletePolicy := metav1.DeletePropagationForeground
    if err := deploymentsClient.Delete(deploy_name, &metav1.DeleteOptions{
        PropagationPolicy: &deletePolicy,
    }); err != nil {
        panic(err)
    }
    fmt.Printf("Deleted %s deployment\n", deploy_name)

    // Delete Service
    if err := servicesClient.Delete(deploy_name, &metav1.DeleteOptions{
        PropagationPolicy: &deletePolicy,
    }); err != nil {
        panic(err)
    }
    fmt.Printf("Deleted %s service\n", deploy_name)
}

func DeployService(deployment *appsv1.Deployment, service *apiv1.Service, namespace string) {

    clientset := setClient()
    deploymentsClient := clientset.AppsV1().Deployments(namespace)


    // Create Deployment
    fmt.Println("Creating deployment...")
    result, err := deploymentsClient.Create(deployment)
    if err != nil {
        panic(err)
    }
    fmt.Printf("Created deployment %q.\n", result.GetObjectMeta().GetName())

    // Create Service
    fmt.Println("Creating service...")
    servicesClient := clientset.CoreV1().Services(namespace)

    result1, err := servicesClient.Create(service)
    if err != nil {
        panic(err)
    }
    fmt.Printf("Created service %q.\n", result1.GetObjectMeta().GetName())

}

func configNamespace (name string, action string) {
    clientset := setClient()
    nameClient := clientset.CoreV1().Namespaces()

    if action == "create" {
        namespace := &apiv1.Namespace{
            ObjectMeta: metav1.ObjectMeta{
                Name: name,
            },
        }
        nameClient.Create(namespace)
        fmt.Printf("Created %s namespace\n", name)
    } else if action == "delete" {
        deletePolicy := metav1.DeletePropagationForeground
        if err := nameClient.Delete(name, &metav1.DeleteOptions{
            PropagationPolicy: &deletePolicy,
        }); err != nil {
            panic(err)
        }
        fmt.Printf("Deleted %s namespace\n", name)
    }
}

func GetServices() *apiv1.ServiceList {

    clientset := setClient()
    services, err := clientset.Core().Services("").List(metav1.ListOptions{})
    for _, service := range services.Items {
        if err != nil {
            panic(err.Error())
        }
        fmt.Printf(" * SERVICE Name: %s\n", service.GetName())
        fmt.Printf("Kind: %s\n", service.Kind)
        fmt.Printf("Labels: %s\n", service.GetLabels())
        fmt.Printf("Type: %s\n", service.Spec.Type)
        //fmt.Printf("External IP: %v\n", service.Spec.ExternalIPs)
        fmt.Printf("Cluster IP: %s\n", service.Spec.ClusterIP)

        for _, port := range service.Spec.Ports {
            fmt.Printf("Port Name: %s, Port# %d, NodePort: %d\n", port.Name, port.Port, port.NodePort)
        }

        for _, ip := range service.Status.LoadBalancer.Ingress {
            fmt.Printf("LB IP: %s \n", ip.IP)
        }
    }
    return services
}

func GetDeployments(namespace string) []appsv1.Deployment {

    clientset := setClient()

    deploymentsClient := clientset.AppsV1().Deployments(namespace)
    list, err := deploymentsClient.List(metav1.ListOptions{})
    if err != nil {
        panic(err)
    }
    for _, d := range list.Items {
        fmt.Printf(" * %s (%d replicas)\n", d.Name, *d.Spec.Replicas)
    }
    return list.Items
}

func GetServicesPortIP(service_name string) (int32, string) {

    clientset := setClient()
    services, err := clientset.Core().Services("").List(metav1.ListOptions{})
    var nodeport int32
    var ipaddress string
    nodeport = 0
    ipaddress = ""
    for _, service := range services.Items {
        if err != nil {
            panic(err.Error())
        }
        if service.GetName() == service_name {
            for _, port := range service.Spec.Ports {
                if port.NodePort > 0 {
                    nodeport = port.NodePort
                }
            }
            for _, ip := range service.Status.LoadBalancer.Ingress {
                    ipaddress = ip.IP
            }
        }
    }

        return nodeport, ipaddress
}

func GetPodsIP(pod_name string, namespace string) []string {

    clientset := setClient()

    var ips []string
    pods, err := clientset.CoreV1().Pods(namespace).List(metav1.ListOptions{})
    if err != nil {
        panic(err)
    }
    for _, pod := range pods.Items {
        if strings.Contains(pod.Name, pod_name) {
            fmt.Println(pod.Name, pod.Status.PodIP)
            ips = append(ips, pod.Status.PodIP)
        }
    }

    return ips
}

func CopyFileToPod(src, dest string) error {

    // dest must be "namespace/podname/containername:<your path>"
    pSplit := strings.Split(dest, ":")
    pathPrefix := pSplit[0]
    pathToCopy := pSplit[1]

    buffer, err := ioutil.ReadFile(src)
    if err != nil {
        fmt.Print(err)
    }

    dir, _ := filepath.Split(pathToCopy)
    command := "mkdir -p " + dir
    _, stderr, err := Exec(pathPrefix, command, nil)

    if err != nil {
        fmt.Print(err)
        fmt.Print(stderr)
        return err
    }

    command = "cp /dev/stdin " + pathToCopy
    stdin := bytes.NewReader(buffer)
    _, stderr, err = Exec(pathPrefix, command, stdin)

    if err != nil {
        fmt.Print(err)
        fmt.Print(stderr)
        return err
    }

    return nil
}


func Exec(pathPrefix, command string, stdin io.Reader) ([]byte, []byte, error) {
        clientset := setClient()
        kubeconfig := filepath.Join(
             os.Getenv("HOME"), ".kube", "config",
        )
        config, err := clientcmd.BuildConfigFromFlags("", kubeconfig)
        if err != nil {
            panic(err.Error())
        }

        prefixSplit := strings.Split(pathPrefix, "/")
        namespace := prefixSplit[0]
        podName := prefixSplit[1]
        containerName := prefixSplit[2]

        req := clientset.Core().RESTClient().Post().
                Resource("pods").
                Name(podName).
                Namespace(namespace).
                SubResource("exec")
        scheme := runtime.NewScheme()
        if err := apiv1.AddToScheme(scheme); err != nil {
                return nil, nil, fmt.Errorf("error adding to scheme: %v", err)
        }

        parameterCodec := runtime.NewParameterCodec(scheme)
        req.VersionedParams(&apiv1.PodExecOptions{
                Command:   strings.Fields(command),
                Container: containerName,
                Stdin:     stdin != nil,
                Stdout:    true,
                Stderr:    true,
                TTY:       false,
        }, parameterCodec)

        exec, err := remotecommand.NewSPDYExecutor(config, "POST", req.URL())
        if err != nil {
                return nil, nil, fmt.Errorf("error while creating Executor: %v", err)
        }

        var stdout, stderr bytes.Buffer
        err = exec.Stream(remotecommand.StreamOptions{
                Stdin:  stdin,
                Stdout: &stdout,
                Stderr: &stderr,
                Tty:    false,
        })
        if err != nil {
                return nil, nil, fmt.Errorf("error in Stream: %v", err)
        }

        return stdout.Bytes(), stderr.Bytes(), nil
}
