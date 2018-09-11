// Copyright (c) Authors of Clover
//
// All rights reserved. This program and the accompanying materials
// are made available under the terms of the Apache License, Version 2.0
// which accompanies this distribution, and is available at
// http://www.apache.org/licenses/LICENSE-2.0

package main

import (
    "encoding/hex"
    "bufio"
    "bytes"
    "encoding/binary"
    "fmt"
    "io"
    "io/ioutil"
    "net/http"
    "os"
    "os/signal"
    "strconv"
    "strings"
    "time"

    "github.com/google/gopacket"
    "github.com/google/gopacket/layers"
    "github.com/iovisor/gobpf/bcc"
    opentracing "github.com/opentracing/opentracing-go"
    jaeger "github.com/uber/jaeger-client-go"
    jaeger_config "github.com/uber/jaeger-client-go/config"
    "github.com/vishvananda/netlink"

    "golang.org/x/sys/unix"

    core_v1 "k8s.io/api/core/v1"
    "k8s.io/apimachinery/pkg/runtime"
    metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
    "k8s.io/client-go/kubernetes"
    "k8s.io/client-go/rest"
    "k8s.io/client-go/tools/remotecommand"
)

/*
#cgo CFLAGS: -I/usr/include/bcc/compat
#cgo LDFLAGS: -lbcc
#include <bcc/bpf_common.h>
#include <bcc/libbpf.h>
*/
import "C"

type session_key_t struct {
    src_ip      uint32
    dst_ip      uint32
    src_port    uint16
    dst_port    uint16
}

type session_t struct {
    Req_time    uint64
    Resp_time   uint64
}

type monitoring_info_t struct {
    svc_name    string
    pod_name    string
    protocol    string
    port_num    uint32
}

type egress_match_t struct {
    dst_ip      uint32
    dst_port    uint16
}

const (
    HTTP = 1 << iota
    HTTP2 = 1 << iota
    TCP = 1 << iota
    UDP = 1 << iota
)

var sessionMap map[string]map[string]string;

var veth_ifidx_command = "cat /sys/class/net/eth0/iflink";

var protocolMap = map[string]int{
    "http":     1,
    "http2":    2,
    "tcp":      3,
    "udp":      4,
}

func linkSetup(ifname string) netlink.Link {
    link, err := netlink.LinkByName(ifname)
    netlink.LinkSetUp(link)
    if err != nil {
        fmt.Println(err)
        return nil
    }
    return link
}

/*
 * dumpBPFTable: for debug purpose
 */
func dumpBPFTable(table *bcc.Table) {
    iterator := table.Iter()
    if iterator == nil {
        fmt.Printf("Table %v does not exist\n", table.Name())
    } else {
        for iterator.Next() {
            key_str, _ := table.KeyBytesToStr(iterator.Key())
            leaf_str, _ := table.LeafBytesToStr(iterator.Leaf())
            fmt.Printf("table %v key: %v  leaf: %v\n", table.Name(), key_str, leaf_str)
        }
    }
}

func print_network_traces(tracer opentracing.Tracer) {
    for key, value := range sessionMap {
        if _, ok := value["done"]; ok {
            span := tracer.StartSpan("http-tracing")
            span.SetTag("Source-IP", value["srcip"])
            span.SetTag("Destination-IP", value["dstip"])
            span.SetTag("Source-Port", value["srcport"])
            span.SetTag("Destination-Port", value["dstport"])
            span.SetTag("HTTP Request Method", value["reqmethod"])
            span.SetTag("HTTP Request URL", value["requrl"])
            span.SetTag("HTTP Request Protocol", value["reqproto"])
            span.SetTag("HTTP Response Status", value["respstatus"])
            span.SetTag("HTTP Response Status Code", value["respstatuscode"])
            span.SetTag("HTTP Response Protocol", value["respproto"])
            span.SetTag("HTTP Session Duration", value["duration"])
            span.Finish()
            delete(sessionMap, key)
        }
    }
}

func handle_skb_event(data *[]byte, session_table *bcc.Table,
                      monitoring_info monitoring_info_t,
                      egress_match_list []egress_match_t) (error) {
    //fmt.Printf("monitoring info has %v\n", monitoring_info)
    fmt.Printf("%s", hex.Dump(*data))
    var src_ip, dst_ip uint32
    var src_port, dst_port uint16
    var session_key, src_ip_str, dst_ip_str string
    proto := HTTP
    is_ingress:= binary.LittleEndian.Uint32((*data)[0:4])
    packet := gopacket.NewPacket((*data)[4:len(*data)],
                                 layers.LayerTypeEthernet,
                                 gopacket.Default)
    if ipv4_layer := packet.Layer(layers.LayerTypeIPv4); ipv4_layer != nil {
        ipv4, _ := ipv4_layer.(*layers.IPv4)
        src_ip_str = ipv4.SrcIP.String()
        dst_ip_str = ipv4.DstIP.String()
        fmt.Printf("Source: %s      Dest: %s\n", src_ip_str, dst_ip_str)
        // Note: the src_ip and dst_ip var here are ONLY being used as
        // lookup key to eBPF hash table, hence preserving network
        // byte order
        src_ip = binary.BigEndian.Uint32(ipv4.SrcIP)
        dst_ip = binary.BigEndian.Uint32(ipv4.DstIP)
    }
    tcp_layer := packet.Layer(layers.LayerTypeTCP)
    if tcp_layer != nil {
        tcp, _ := tcp_layer.(*layers.TCP)
        fmt.Printf("From src port %d to dst port %d [%v]: FIN:%v|SYN:%v|RST:%v|PSH:%v|ACK:%v|URG:%v|ECE:%v|CWR:%v|NS:%v\n",
                    tcp.SrcPort, tcp.DstPort, tcp.DataOffset, tcp.FIN, tcp.SYN,
                    tcp.RST, tcp.PSH, tcp.ACK, tcp.URG, tcp.ECE, tcp.CWR, tcp.NS)
        //src_port := binary.LittleEndian.Uint16(uint16(tcp.SrcPort))
        //dst_port := binary.LittleEndian.Uint16(uint16(tcp.DstPort))
        src_port = uint16(tcp.SrcPort)
        dst_port = uint16(tcp.DstPort)
    } else {
        fmt.Printf("Non-TCP packet, skip tracing...\n")
        return nil
    }
    fmt.Printf("proto: %d is_ingress: %d data length %v\n", proto, is_ingress, len(*data))
    fmt.Println("dst_port is ", dst_port)
    if dst_port == 0 {
        return nil
    }
    // SKW: dump table
    dumpBPFTable(session_table)
    egress_port_req := false
    for _, port := range egress_match_list {
        if port.dst_port == dst_port {
            egress_port_req = true
            break
        }
    }
    app_layer := packet.ApplicationLayer()
    if app_layer == nil {
        fmt.Printf("No application layer, TCP packet\n")
        proto = TCP
    }
    if dst_port == uint16(monitoring_info.port_num) || egress_port_req {
        session_key = fmt.Sprintf("%x.%x:%d:%d", src_ip, dst_ip, src_port,
                                  dst_port)
        if _, ok := sessionMap[session_key]; !ok {
            sessionMap[session_key] = make(map[string]string)
        }
        map_val := sessionMap[session_key]
        map_val["srcip"] = src_ip_str
        map_val["dstip"] = dst_ip_str
        map_val["srcport"] = fmt.Sprintf("%d", src_port)
        map_val["dstport"] = fmt.Sprintf("%d", dst_port)
        if proto == HTTP {
            reader := bytes.NewReader(app_layer.Payload())
            buf := bufio.NewReader(reader)
            req, err := http.ReadRequest(buf)
            if err != nil {
                fmt.Printf("Request error: ")
                fmt.Println(err)
            } else if req == nil {
                fmt.Println("request is nil")
            } else {
                fmt.Printf("HTTP Request Method %s url %v proto %v\n",
                            req.Method, req.URL, req.Proto)
                map_val["reqmethod"] = req.Method
                map_val["requrl"] = fmt.Sprintf("%v", req.URL)
                map_val["reqproto"] = fmt.Sprintf("%v", req.Proto)
                if _, ok := map_val["respstatus"]; ok {
                    map_val["done"] = "true"
                }
            }
        }
    } else {
        session_key := session_key_t {
            src_ip: dst_ip,
            dst_ip: src_ip,
            src_port:   dst_port,
            dst_port:   src_port,
        }
        key_buf := &bytes.Buffer{}
        err := binary.Write(key_buf, binary.LittleEndian, session_key)
        if err != nil {
            fmt.Println(err)
            return nil
        }
        key := append([]byte(nil), key_buf.Bytes()...)
        if leaf, err := session_table.Get(key); err != nil {
            fmt.Printf("Failed to lookup key %v with err %v\n", session_key, err)
            return nil
        } else {
            leaf_buf := bytes.NewBuffer(leaf)
            if leaf_buf == nil {
                fmt.Println("Error: leaf is nil")
                return nil
            }
            session := session_t{}
            if err = binary.Read(leaf_buf, binary.LittleEndian, &session);
                err != nil {
                fmt.Println(err)
                return nil
            }
            if session.Resp_time == 0 {
                fmt.Printf("session response time not set?\n")
                return nil
            }
            duration := (session.Resp_time - session.Req_time)/1000
            fmt.Printf("Leaf %v\n", leaf)
            fmt.Printf("Duration: %d usec\n", duration)
            sess_key := fmt.Sprintf("%x.%x:%d:%d", dst_ip, src_ip,
                                    dst_port, src_port)
            if _, ok := sessionMap[sess_key]; !ok {
                sessionMap[sess_key] = make(map[string]string)
            }
            map_val := sessionMap[sess_key]
            map_val["srcip"] = dst_ip_str
            map_val["dstip"] = src_ip_str
            map_val["srcport"] = fmt.Sprintf("%d", dst_port)
            map_val["dstport"] = fmt.Sprintf("%d", src_port)

            if proto == HTTP {
                reader := bytes.NewReader(app_layer.Payload())
                buf := bufio.NewReader(reader)
                resp, err := http.ReadResponse(buf, nil)
                if err != nil {
                    fmt.Printf("Response error: ")
                    fmt.Println(err)
                    return nil
                } else if resp == nil {
                    fmt.Println("response is nil")
                } else {
                    fmt.Printf("HTTP Response Status %v code %v Proto %v\n",
                                resp.Status, resp.StatusCode, resp.Proto)
                    map_val["respstatus"] = resp.Status
                    map_val["respstatuscode"] = fmt.Sprintf("%v", resp.StatusCode)
                    map_val["respproto"] = fmt.Sprintf("%v", resp.Proto)
                    map_val["duration"] = fmt.Sprintf("%v usec", duration)
                    if _, ok := map_val["reqmethod"]; ok {
                        map_val["done"] = "true"
                    }
                }
                resp.Body.Close()
            }
        }
    }

    return nil
}

func get_monitoring_pod(node_name string) (label_key string,
                                           label_value string,
                                           namespace string,
                                           err error) {
    // TODO(s3wong): hardcode for now
    return "app", "proxy", "default", nil
}

func get_egress_match_list() []egress_match_t {
    ret_list := make([]egress_match_t, 0, 1)
    ret_list = append(ret_list, egress_match_t{0, 80})
    return ret_list
}

// initJaeger returns an instance of Jaeger Tracer that samples 100% of traces and logs all spans to stdout.
func initJaeger(service string) (opentracing.Tracer, io.Closer) {
    cfg := &jaeger_config.Configuration{
        Sampler: &jaeger_config.SamplerConfig{
            Type:  "const",
            Param: 1,
        },
        Reporter: &jaeger_config.ReporterConfig{
            LogSpans: true,
            CollectorEndpoint: "http://jaeger-collector:14268/api/traces",
            LocalAgentHostPort: "jaeger-agent:6831",
        },
    }
    tracer, closer, err := cfg.New(service, jaeger_config.Logger(jaeger.StdLogger))
    if err != nil {
        panic(fmt.Sprintf("ERROR: cannot init Jaeger: %v\n", err))
    }
    return tracer, closer
}

func main() {

    var monitoring_info = monitoring_info_t{}

    config, err := rest.InClusterConfig()
    if err != nil {
        panic(err.Error())
    }

    client, err := kubernetes.NewForConfig(config)
    if err != nil {
        panic(err.Error())
    }

    // TODO(s3wong): make sure the pod exists
    // if it doesn't, should get into wait loop
    /*
    pod, err := client.CoreV1().Pods("").Get(target_pod_name, metav1.GetOptions{})
    if err != nil {
        panic(err.Error())
    }
    */
    node_name := os.Getenv("MY_NODE_NAME")

    label_key, label_val, target_namespace, err := get_monitoring_pod(node_name)
    if err != nil {
        fmt.Printf("Error while trying to find pod to monioring: %v\n", err.Error())
        return
    }

    label_selector := fmt.Sprintf("%s=%s", label_key, label_val)
    var target_container_name string
    svc_map := make(map[string][]string)
    if svcs, err := client.CoreV1().Services(target_namespace).List(metav1.ListOptions{
                LabelSelector: label_selector,
                        }); err != nil {
        fmt.Printf("Error fetching services with label %v:%v - %v\n",
                    label_key, label_val, err.Error())
        return
    } else {
        for _, svc := range svcs.Items {
            // TODO(s3wong): currently only assuming one service port
            svc_port := svc.Spec.Ports[0]
            target_port := svc_port.TargetPort.String()
            svc_port_name := svc_port.Name
            svc_map[target_port] = append(svc_map[target_port], svc.GetName())
            if len(svc_port_name) > 0 {
                svc_map[target_port] = append(svc_map[target_port], svc_port_name)
            } else {
                svc_map[target_port] = append(svc_map[target_port], "tcp")
            }
        }
    }
    if pods, err := client.CoreV1().Pods(target_namespace).List(metav1.ListOptions{
                LabelSelector: label_selector,
                        }); err != nil {
        fmt.Printf("Error fetching pods with label %v:%v - %v\n",
                    label_key, label_val, err.Error())
        return
    } else {
        found := false
        for _, v := range pods.Items {
            if v.Spec.NodeName == node_name {
                // TODO(s3wong): just one pod will be monitored for now
                monitoring_info.pod_name = v.GetName()
                target_container_name = v.Spec.Containers[0].Name
                monitoring_info.port_num = uint32(v.Spec.Containers[0].Ports[0].ContainerPort)
                tp_string := strconv.Itoa(int(monitoring_info.port_num))
                svc_array := svc_map[tp_string]
                monitoring_info.svc_name = svc_array[0]
                if (strings.Contains(svc_array[1], "-")) {
                    monitoring_info.protocol = svc_array[1][:strings.Index(svc_array[1], "-")]
                } else {
                    monitoring_info.protocol = svc_array[1]
                }
                found = true
                break
            }
        }
        if !found {
            fmt.Printf("No pod found in namespace %v\n", target_namespace)
            return
        }
    }

    // Following code based on:
    // https://stackoverflow.com/questions/43314689/example-of-exec-in-k8ss-pod-by-using-go-client
    // https://github.com/a4abhishek/Client-Go-Examples/blob/master/exec_to_pod/exec_to_pod.go

    exec_req := client.CoreV1().RESTClient().Post().
            Resource("pods").
            Name(monitoring_info.pod_name).
            Namespace(target_namespace).
            SubResource("exec")
    scheme := runtime.NewScheme()
    if err := core_v1.AddToScheme(scheme); err != nil {
        panic(err.Error())
    }

    parameterCodec := runtime.NewParameterCodec(scheme)
    exec_req.VersionedParams(&core_v1.PodExecOptions{
            Command:    strings.Fields(veth_ifidx_command),
            Container:  target_container_name,
            Stdin:      false,
            Stdout:     true,
            Stderr:     true,
            TTY:        false,
        }, parameterCodec)

    exec, err := remotecommand.NewSPDYExecutor(config, "POST", exec_req.URL())
    if err != nil {
        panic(err.Error())
    }

    var stdout, stderr bytes.Buffer
    err = exec.Stream(remotecommand.StreamOptions{
            Stdin:  nil,
            Stdout: &stdout,
            Stderr: &stderr,
            Tty:    false,
        })
    if err != nil {
        panic(err.Error())
    }

    stdout_no_newline := strings.TrimSuffix(stdout.String(), "\n")
    ifindex , err := strconv.Atoi(stdout_no_newline)
    if err != nil {
        fmt.Printf("Error converting %v to ifindex, error: %v\n", stdout, err.Error())
        return
    }

    sessionMap = map[string]map[string]string{};

    fmt.Println("Begin network tracing")

    buf, err := ioutil.ReadFile("ebpf/session_tracking.c")
    if err != nil {
        fmt.Println(err)
        return
    }
    code := string(buf)

    bpf_mod := bcc.NewModule(code, []string{})
    defer bpf_mod.Close()

    ingress_fn, err := bpf_mod.Load("handle_ingress",
                                    C.BPF_PROG_TYPE_SCHED_CLS,
                                    1, 65536)
    if err != nil {
        fmt.Println("Failed to load ingress func: %v\n", err)
        return
    }
    fmt.Println("Loaded Ingress func to structure")

    egress_fn, err := bpf_mod.Load("handle_egress",
                                   C.BPF_PROG_TYPE_SCHED_CLS,
                                   1, 65536)
    if err != nil {
        fmt.Println("Failed to load egress func: %v\n", err)
        return
    }

    fmt.Println("Loaded Egress func to structure")

    traffic_table := bcc.NewTable(bpf_mod.TableId("dports2proto"), bpf_mod)
    key, _ := traffic_table.KeyStrToBytes(strconv.Itoa(int(monitoring_info.port_num)))
    leaf, _ := traffic_table.LeafStrToBytes(strconv.Itoa(protocolMap[monitoring_info.protocol]))
    if err := traffic_table.Set(key, leaf); err != nil {
        fmt.Printf("Failed to set traffic table tcpdports: %v\n", err)
        return
    }

    // SKW: debug, dump table
    dumpBPFTable(traffic_table)

    egress_match_list := get_egress_match_list()

    egress_table := bcc.NewTable(bpf_mod.TableId("egress_lookup_table"), bpf_mod)
    for _, egress_match := range egress_match_list {
        key_buf := &bytes.Buffer{}
        err := binary.Write(key_buf, binary.LittleEndian, egress_match)
        if err != nil {
            fmt.Printf("Error converting key %v into binary: %v\n", egress_match, err)
            continue
        }
        key := append([]byte(nil), key_buf.Bytes()...)
        leaf, _ := egress_table.LeafStrToBytes(strconv.Itoa(1))
        if err := egress_table.Set(key, leaf); err != nil {
            fmt.Printf("Failed to add key %v:%v to egress table: %v\n", key,leaf,err)
            return
        }
    }

    session_table := bcc.NewTable(bpf_mod.TableId("sessions"), bpf_mod)

    attrs := netlink.QdiscAttrs {
        //LinkIndex: link.Attrs().Index,
        LinkIndex: ifindex,
        Handle: netlink.MakeHandle(0xffff, 0),
        Parent: netlink.HANDLE_CLSACT,
    }

    qdisc := &netlink.GenericQdisc {
        QdiscAttrs: attrs,
        QdiscType:  "clsact",
    }

    if err := netlink.QdiscAdd(qdisc); err != nil {
        fmt.Println(err)
        return
    }

    fmt.Println("Qdisc for clsact added for index 11")

    ingress_filter_attrs := netlink.FilterAttrs{
        //LinkIndex:  link.Attrs().Index,
        LinkIndex:  ifindex,
        //Parent:     netlink.MakeHandle(0xffff, 0xfff2),
        Parent:     netlink.MakeHandle(0xffff, 0xfff3),
        Priority:   1,
        Protocol:   unix.ETH_P_ALL,
    }
    ingress_filter := &netlink.BpfFilter{
        FilterAttrs:    ingress_filter_attrs,
        Fd:             ingress_fn,
        Name:           "handle_ingress",
        DirectAction:   true,
    }
    if ingress_filter.Fd < 0 {
        fmt.Println("Failed to load ingress bpf program")
        return
    }

    if err := netlink.FilterAdd(ingress_filter); err != nil {
        fmt.Println(err)
        return
    }

    egress_filter_attrs := netlink.FilterAttrs{
        //LinkIndex:  link.Attrs().Index,
        LinkIndex:  ifindex,
        //Parent:     netlink.MakeHandle(0xffff, 0xfff3),
        Parent:     netlink.MakeHandle(0xffff, 0xfff2),
        Priority:   1,
        Protocol:   unix.ETH_P_ALL,
    }
    egress_filter := &netlink.BpfFilter{
        FilterAttrs:    egress_filter_attrs,
        Fd:             egress_fn,
        Name:           "handle_egress",
        DirectAction:   true,
    }
    if egress_filter.Fd < 0 {
        fmt.Println("Failed to load egress bpf program")
        return
    }

    if err := netlink.FilterAdd(egress_filter); err != nil {
        fmt.Println(err)
        return
    }

    table := bcc.NewTable(bpf_mod.TableId("skb_events"), bpf_mod)

    skb_rev_chan := make(chan []byte)

    perfMap, err := bcc.InitPerfMap(table, skb_rev_chan)
    if err != nil {
        fmt.Println(err)
        return
    }

    tracer, closer := initJaeger(monitoring_info.pod_name)
    defer closer.Close()

    sig := make(chan os.Signal, 1)
    signal.Notify(sig, os.Interrupt, os.Kill)

    go func() {
        for {
            data := <-skb_rev_chan
            /* err := binary.Read(bytes.NewBuffer(data), binary.LittleEndian, &event)
            if err != nil {
                fmt.Printf("failed to decode received data: %s\n", err)
                continue
            }
            */
            err = handle_skb_event(&data, session_table, monitoring_info, egress_match_list)
            if err != nil {
                fmt.Printf("failed to decode received data: %s\n", err)
                continue
            }
        }
    }()

    ticker := time.NewTicker(2 * time.Second)
    stop := make(chan struct{})
    go func() {
        for {
            select {
                case <- ticker.C:
                    print_network_traces(tracer)
                case <- stop:
                    ticker.Stop()
                    return
            }
        }
    }()

    perfMap.Start()
    <-sig
    perfMap.Stop()
}
