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
    "github.com/ghodss/yaml"
    "encoding/json"

    appsv1 "k8s.io/api/apps/v1"
    v1beta1 "k8s.io/api/apps/v1beta1"
    v1beta1ext "k8s.io/api/extensions/v1beta1"
    apiv1 "k8s.io/api/core/v1"
    rbacv1 "k8s.io/api/rbac/v1"
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

// Create various K8s resources
func CreateResource(input_yaml string, resource_type string,
                    image string, namespace string) {
    if namespace == "" {
        namespace = "clover-system"
    }
    // Check path from cloverctl first
    exe_path, err := os.Executable()
    abs_input_yaml := strings.Replace(exe_path, "cloverctl", "", -1) +
                      "/yaml/" + input_yaml
    if _, err := os.Stat(abs_input_yaml); !os.IsNotExist(err) {
        input_yaml = abs_input_yaml
    }
    in, err := ioutil.ReadFile(input_yaml)
    if err != nil {
        fmt.Println("Please specify a valid manifest yaml file")
        return
    }
    out_json, err := yaml.YAMLToJSON(in)
    if err != nil {
        panic(err.Error())
    }

    switch resource_type {
        case "deployment":
            deploy := v1beta1.Deployment{}
            err = json.Unmarshal(out_json, &deploy)
            CreateDeployment(&deploy, namespace)
            deploy.Spec.Template.Spec.Containers[0].Image = image
            fmt.Printf("Image: %s\n",
                              deploy.Spec.Template.Spec.Containers[0].Image)
        case "service":
            service := apiv1.Service{}
            err = json.Unmarshal(out_json, &service)
            CreateService(&service, namespace)
        case "serviceaccount":
            sa := apiv1.ServiceAccount{}
            err = json.Unmarshal(out_json, &sa)
            CreateServiceAccount(&sa, namespace)
        case "clusterrolebinding":
            clusterrolebinding := rbacv1.ClusterRoleBinding{}
            err = json.Unmarshal(out_json, &clusterrolebinding)
            CreateCRB(&clusterrolebinding)
        case "statefulset":
            statefulset := appsv1.StatefulSet{}
            err = json.Unmarshal(out_json, &statefulset)
            CreateStatefulSet(&statefulset, namespace)
        case "pod":
            pod := apiv1.Pod{}
            err = json.Unmarshal(out_json, &pod)
            CreatePod(&pod, namespace)
        case "daemonset":
            daemon := v1beta1ext.DaemonSet{}
            err = json.Unmarshal(out_json, &daemon)
            CreateDaemonSet(&daemon, namespace)
            daemon.Spec.Template.Spec.Containers[0].Image = image
            fmt.Printf("Image: %s\n",
                              daemon.Spec.Template.Spec.Containers[0].Image)

        default:
            fmt.Println("No resource selected")
    }
}

// Delete K8s resources
func DeleteResource(deploy_name string, resource_type string,
                    namespace string) {
    clientset := setClient()
    deletePolicy := metav1.DeletePropagationForeground

    switch resource_type {
        case "deployment":
            deploymentsClient := clientset.AppsV1().Deployments(namespace)
            if err := deploymentsClient.Delete(deploy_name,
                                               &metav1.DeleteOptions{
                PropagationPolicy: &deletePolicy,
            }); err != nil {
                fmt.Printf("Error deleting %v: %v\n", resource_type, err)
                return
            }
        case "service":
            servicesClient := clientset.CoreV1().Services(namespace)
            if err := servicesClient.Delete(deploy_name, &metav1.DeleteOptions{
                PropagationPolicy: &deletePolicy,
            }); err != nil {
                fmt.Printf("Error deleting %v: %v\n", resource_type, err)
                return
            }
        case "serviceaccount":
            saClient := clientset.CoreV1().ServiceAccounts(namespace)
            if err := saClient.Delete(deploy_name, &metav1.DeleteOptions{
                PropagationPolicy: &deletePolicy,
            }); err != nil {
                fmt.Printf("Error deleting %v: %v\n", resource_type, err)
                return
            }
        case "clusterrolebinding":
            crbClient := clientset.RbacV1().ClusterRoleBindings()
            if err := crbClient.Delete(deploy_name, &metav1.DeleteOptions{
                PropagationPolicy: &deletePolicy,
            }); err != nil {
                fmt.Printf("Error deleting %v: %v\n", resource_type, err)
                return
            }
        case "statefulset":
              statefulClient := clientset.AppsV1().StatefulSets(namespace)
            if err := statefulClient.Delete(deploy_name, &metav1.DeleteOptions{
                PropagationPolicy: &deletePolicy,
            }); err != nil {
                fmt.Printf("Error deleting %v: %v\n", resource_type, err)
                return
            }
        case "pod":
            podClient := clientset.CoreV1().Pods(namespace)
            if err := podClient.Delete(deploy_name, &metav1.DeleteOptions{
                PropagationPolicy: &deletePolicy,
            }); err != nil {
                fmt.Printf("Error deleting %v: %v\n", resource_type, err)
                return
            }
        case "daemonset":
            daemonsClient := clientset.AppsV1().DaemonSets(namespace)
            if err := daemonsClient.Delete(deploy_name,
                                               &metav1.DeleteOptions{
                PropagationPolicy: &deletePolicy,
            }); err != nil {
                fmt.Printf("Error deleting %v: %v\n", resource_type, err)
                return
            }
    }
    fmt.Printf("Deleted %s %s\n", deploy_name, resource_type)
}

// Create ServiceAccount
func CreateServiceAccount(sa *apiv1.ServiceAccount, namespace string) {
    clientset := setClient()
    saClient := clientset.CoreV1().ServiceAccounts(namespace)
    result, err  := saClient.Create(sa)
    if err != nil {
        fmt.Printf("Error creating serviceaccount: %v\n", err); return
    }
    fmt.Printf("Created serviceaccount %q.\n",
               result.GetObjectMeta().GetName())
}

// Create ClusterRoleBinding
func CreateCRB(sa *rbacv1.ClusterRoleBinding) {
    clientset := setClient()
    crbClient := clientset.RbacV1().ClusterRoleBindings()
    result, err  := crbClient.Create(sa)
    if err != nil {
        fmt.Printf("Error creating clusterrolebinding: %v\n", err); return
    }
    fmt.Printf("Created clusterrolebinding %q.\n",
               result.GetObjectMeta().GetName())
}

// Create DaemonSet
func CreateDaemonSet(daemonset *v1beta1ext.DaemonSet, namespace string) {
    clientset := setClient()
    daemonsClient := clientset.ExtensionsV1beta1().DaemonSets(namespace)
    result, err := daemonsClient.Create(daemonset)
    if err != nil {
        fmt.Printf("Error creating daemonset: %v\n", err); return
    }
    fmt.Printf("Created daemonset %q.\n", result.GetObjectMeta().GetName())
}

// Create Deployment
func CreateDeployment(deployment *v1beta1.Deployment, namespace string) {
    clientset := setClient()
    deploymentsClient := clientset.AppsV1beta1().Deployments(namespace)
    result, err := deploymentsClient.Create(deployment)
    if err != nil {
        fmt.Printf("Error creating deployment: %v\n", err); return
    }
    fmt.Printf("Created deployment %q.\n", result.GetObjectMeta().GetName())
}

// Create StatefulSet
func CreateStatefulSet(statefulset *appsv1.StatefulSet, namespace string) {
    clientset := setClient()
    statefulsetClient := clientset.AppsV1().StatefulSets(namespace)
    result, err := statefulsetClient.Create(statefulset)
    if err != nil {
        fmt.Printf("Error creating statefulset: %v\n", err); return
    }
    fmt.Printf("Created statefulset %q.\n", result.GetObjectMeta().GetName())
}

// Create Pod
func CreatePod(pod *apiv1.Pod, namespace string) {
    clientset := setClient()
    podClient := clientset.CoreV1().Pods(namespace)
    result, err := podClient.Create(pod)
    if err != nil {
        fmt.Printf("Error creating pod: %v\n", err); return
        panic(err)
    }
    fmt.Printf("Created pod %q.\n", result.GetObjectMeta().GetName())
}

// Create Service
func CreateService(service *apiv1.Service, namespace string) {
    clientset := setClient()
    servicesClient := clientset.CoreV1().Services(namespace)

    result1, err := servicesClient.Create(service)
    if err != nil {
        fmt.Printf("Error creating service: %v\n", err); return
    }
    fmt.Printf("Created service %q\n", result1.GetObjectMeta().GetName())
}

// Create or delete namespace
func ConfigNamespace (name string, action string) {
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
            fmt.Printf("Error deleting namespace: %v\n", err); return
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
        fmt.Printf("Cluster IP: %s\n", service.Spec.ClusterIP)

        for _, port := range service.Spec.Ports {
            fmt.Printf("Port Name: %s, Port# %d, NodePort: %d\n",
                       port.Name, port.Port, port.NodePort)
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
