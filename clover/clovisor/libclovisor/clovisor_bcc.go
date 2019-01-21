// Copyright (c) Authors of Clover
//
// All rights reserved. This program and the accompanying materials
// are made available under the terms of the Apache License, Version 2.0
// which accompanies this distribution, and is available at
// http://www.apache.org/licenses/LICENSE-2.0

package clovisor

import (
    "encoding/hex"
    "bufio"
    "bytes"
    "encoding/binary"
    "fmt"
    "io/ioutil"
    "net/http"
    "strconv"
    "time"

    "github.com/google/gopacket"
    "github.com/google/gopacket/layers"
    "github.com/iovisor/gobpf/bcc"
    opentracing "github.com/opentracing/opentracing-go"
    "github.com/vishvananda/netlink"

    "golang.org/x/sys/unix"
)

/*
#cgo CFLAGS: -I/usr/include/bcc/compat
#cgo LDFLAGS: -lbcc
#include <bcc/bpf_common.h>
#include <bcc/libbpf.h>
*/
import "C"

type ClovisorBCC struct {
    stopChan    chan bool
    // TODO(s3wong): remove once k8s watcher available
    qdisc       *netlink.GenericQdisc
}

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

type egress_match_t struct {
    dst_ip      uint32
    dst_port    uint16
}

type egress_match_cfg struct {
    egress_match    egress_match_t
    action          string
    params          string
}

type session_info_t struct {
    session     map[string]string
    buf         []byte
}

const (
    HTTP = 1 << iota
    HTTP2 = 1 << iota
    TCP = 1 << iota
    UDP = 1 << iota
)

//var sessionMap map[string]map[string]string;
var sessionMap map[string]session_info_t;

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
    for key, sess_info := range sessionMap {
        value := sess_info.session
        if _, ok := value["done"]; ok {
            span := tracer.StartSpan("http-tracing")
            span.SetTag("Node-Name", value["nodename"])
            span.SetTag("Pod-Name", value["podname"])
            span.SetTag("Source-IP", value["srcip"])
            span.SetTag("Destination-IP", value["dstip"])
            span.SetTag("Source-Port", value["srcport"])
            span.SetTag("Destination-Port", value["dstport"])
            span.SetTag("HTTP Request Method", value["reqmethod"])
            span.SetTag("HTTP Request URL", value["requrl"])
            span.SetTag("HTTP Request Protocol", value["reqproto"])
            if _, exist := value["host"]; exist {
                span.SetTag("HTTP Request Host", value["host"])
            }
            if _, exist := value["useragent"]; exist {
                span.SetTag("HTTP Client User Agent", value["useragent"])
            }
            if _, exist := value["requestid"]; exist {
                span.SetTag("OpenTracing Request ID", value["requestid"])
            }
            if _, exist := value["envoydecorator"]; exist {
                span.SetTag("Envoy Decorator", value["envoydecorator"])
            }
            if _, exist := value["traceid"]; exist {
                span.SetTag("Trace ID", value["traceid"])
            }
            span.SetTag("HTTP Request Packet Count", value["reqpakcount"])
            span.SetTag("HTTP Request Byte Count", value["reqbytecount"])
            span.SetTag("HTTP Response Status", value["respstatus"])
            span.SetTag("HTTP Response Status Code", value["respstatuscode"])
            span.SetTag("HTTP Response Protocol", value["respproto"])
            span.SetTag("HTTP Response Packet Count", value["resppakcount"])
            span.SetTag("HTTP Response Byte Count", value["respbytecount"])
            span.SetTag("HTTP Session Duration", value["duration"])
            span.Finish()
            delete(sessionMap, key)
        }
    }
}

func handle_skb_event(data *[]byte, node_name string, pod_name string,
                      session_table *bcc.Table,
                      monitoring_info *monitoring_info_t,
                      egress_match_list []egress_match_t) (error) {
    //fmt.Printf("monitoring info has %v\n", monitoring_info)
    fmt.Printf("\n\nnode[%s] pod[%s]\n%s", node_name, pod_name, hex.Dump(*data))
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
    // TODO(s3wong): dump table
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
            sessionMap[session_key] = session_info_t{}
            sess_map := sessionMap[session_key]
            sess_map.session = make(map[string]string)
            sess_map.buf = []byte{}
            sessionMap[session_key] = sess_map
            zero := strconv.Itoa(0)
            sessionMap[session_key].session["reqpakcount"] = zero
            sessionMap[session_key].session["reqbytecount"] = zero
            sessionMap[session_key].session["resppakcount"] = zero
            sessionMap[session_key].session["respbytecount"] = zero
        }
        map_val := sessionMap[session_key].session
        map_val["nodename"] = node_name
        map_val["podname"] = pod_name
        map_val["srcip"] = src_ip_str
        map_val["dstip"] = dst_ip_str
        map_val["srcport"] = fmt.Sprintf("%d", src_port)
        map_val["dstport"] = fmt.Sprintf("%d", dst_port)
        curr_pak_count, _ := strconv.Atoi(map_val["reqpakcount"])
        curr_byte_count, _ := strconv.Atoi(map_val["reqbytecount"])
        curr_pak_count++
        if proto == HTTP {
            curr_byte_count += len(app_layer.Payload())
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
                if user_agent := req.UserAgent(); len(user_agent) > 0 {
                    map_val["useragent"] = user_agent
                }
                if len(req.Host) > 0 {
                    map_val["host"] = req.Host
                }
                header := req.Header
                if req_id := header.Get("X-Request-Id"); len(req_id) > 0 {
                    map_val["requestid"] = req_id
                }
                if envoy_dec := header.Get("X-Envoy-Decorator-Operation"); len(envoy_dec) > 0 {
                    map_val["envoydecorator"] = envoy_dec
                }
                if trace_id := header.Get("X-B3-Traceid"); len(trace_id) > 0 {
                    map_val["traceid"] = trace_id
                }
                if _, ok := map_val["respstatus"]; ok {
                    map_val["done"] = "true"
                }
            }
        } else {
            // TODO(s3wong): TCP assumed for now
            curr_byte_count += (len(*data) - 4)
        }
        map_val["reqpakcount"] = strconv.Itoa(curr_pak_count)
        map_val["reqbytecount"] = strconv.Itoa(curr_byte_count)
        fmt.Printf("Current session packet count %v and byte count %v\n", map_val["reqpakcount"], map_val["reqbytecount"])
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
            var duration uint64 = 0
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
            } else {
                duration = (session.Resp_time - session.Req_time)/1000
                fmt.Printf("Leaf %v\n", leaf)
                fmt.Printf("Duration: %d usec\n", duration)
            }
            sess_key := fmt.Sprintf("%x.%x:%d:%d", dst_ip, src_ip,
                                    dst_port, src_port)
            if _, ok := sessionMap[sess_key]; !ok {
                //sessionMap[sess_key] = make(map[string]string)
                sessionMap[sess_key] = session_info_t{}
                sess_map := sessionMap[sess_key]
                sess_map.session = make(map[string]string)
                sess_map.buf = []byte{}
                sessionMap[sess_key] = sess_map
                zero := strconv.Itoa(0)
                sessionMap[sess_key].session["reqpakcount"] = zero
                sessionMap[sess_key].session["reqbytecount"] = zero
                sessionMap[sess_key].session["resppakcount"] = zero
                sessionMap[sess_key].session["respbytecount"] = zero
            }
            var map_val = sessionMap[sess_key].session
            map_val["nodename"] = node_name
            map_val["podname"] = pod_name
            map_val["srcip"] = dst_ip_str
            map_val["dstip"] = src_ip_str
            map_val["srcport"] = fmt.Sprintf("%d", dst_port)
            map_val["dstport"] = fmt.Sprintf("%d", src_port)
            map_val["duration"] = fmt.Sprintf("%v usec", duration)
            curr_pak_count, _ := strconv.Atoi(map_val["resppakcount"])
            curr_byte_count, _ := strconv.Atoi(map_val["respbytecount"])
            curr_pak_count++

            if proto == HTTP {
                curr_byte_count += len(app_layer.Payload())
                reader := bytes.NewReader(app_layer.Payload())
                buf := bufio.NewReader(reader)
                resp, err := http.ReadResponse(buf, nil)
                read_http := true
                if err != nil {
                    fmt.Printf("Response error: ")
                    fmt.Println(err)
                    sess_map := sessionMap[sess_key]
                    sess_map.buf = append(sess_map.buf, app_layer.Payload()...)
                    reader = bytes.NewReader(sess_map.buf)
                    buf = bufio.NewReader(reader)
                    resp, err = http.ReadResponse(buf, nil)
                    if err != nil || resp == nil {
                        if err != nil {
                            fmt.Printf("Response error: %v\n", err)
                        }
                        read_http = false
                    }
                    sessionMap[sess_key] = sess_map
                } else if resp == nil {
                    fmt.Println("response is nil")
                    read_http = false
                }
                if read_http {
                    fmt.Printf("HTTP Response Status %v code %v Proto %v\n",
                                resp.Status, resp.StatusCode, resp.Proto)
                    map_val["respstatus"] = resp.Status
                    map_val["respstatuscode"] = fmt.Sprintf("%v", resp.StatusCode)
                    map_val["respproto"] = fmt.Sprintf("%v", resp.Proto)
                    //map_val["duration"] = fmt.Sprintf("%v usec", duration)
                    /*
                    if _, ok := map_val["reqmethod"]; ok {
                        map_val["done"] = "true"
                    }
                    */
                }
                if resp != nil {
                    resp.Body.Close()
                }
            } else {
                // TODO(s3wong): TCP assumed for now
                curr_byte_count += (len(*data) - 4)
            }
            map_val["resppakcount"] = strconv.Itoa(curr_pak_count)
            map_val["respbytecount"] = strconv.Itoa(curr_byte_count)
            fmt.Printf("Current session packet count %v and byte count %v\n", map_val["resppakcount"], map_val["respbytecount"])
            if duration > 0 {
                map_val["done"] = "true"
            }
        }
    }

    return nil
}

func setTrafficTable(traffic_table *bcc.Table, port_num int, protocol_id string, dump_table bool) error {
    key, _ := traffic_table.KeyStrToBytes(strconv.Itoa(port_num))
    leaf, _ := traffic_table.LeafStrToBytes(strconv.Itoa(protocolMap[protocol_id]))
    if err := traffic_table.Set(key, leaf); err != nil {
        fmt.Printf("Failed to set traffic table tcpdports: %v\n", err)
        return err
    }
    if dump_table {
        dumpBPFTable(traffic_table)
    }
    return nil
}

func setEgressTable(egress_table *bcc.Table,
                    egress_match_list []egress_match_t,
                    action int,
                    dump_table bool) error {
    for _, egress_match := range egress_match_list {
        key_buf := &bytes.Buffer{}
        err := binary.Write(key_buf, binary.LittleEndian, egress_match)
        if err != nil {
            fmt.Printf("Error converting key %v into binary: %v\n", egress_match, err)
            continue
        }
        key := append([]byte(nil), key_buf.Bytes()...)
        leaf, _ := egress_table.LeafStrToBytes(strconv.Itoa(action))
        if err := egress_table.Set(key, leaf); err != nil {
            fmt.Printf("Failed to add key %v:%v to egress table: %v\n", key,leaf,err)
            return err
        }
    }
    if dump_table {
        dumpBPFTable(egress_table)
    }
    return nil
}

func ClovisorNewPodInit(k8s_client *ClovisorK8s,
                        node_name string,
                        pod_name string,
                        monitoring_info *monitoring_info_t) (*ClovisorBCC, error) {

    output, err := k8s_client.exec_command(veth_ifidx_command, monitoring_info)
    if err != nil {
        return nil, err
    }

    ifindex , err := strconv.Atoi(output)
    if err != nil {
        fmt.Printf("Error converting %v to ifindex, error: %v\n", output, err.Error())
        return nil, err
    }

    sessionMap = map[string]session_info_t{};

    fmt.Printf("Beginning network tracing for pod %v\n", pod_name)

    buf, err := ioutil.ReadFile("libclovisor/ebpf/session_tracking.c")
    if err != nil {
        fmt.Println(err)
        return nil, err
    }
    code := string(buf)

    bpf_mod := bcc.NewModule(code, []string{})
    //defer bpf_mod.Close()

    ingress_fn, err := bpf_mod.Load("handle_ingress",
                                    C.BPF_PROG_TYPE_SCHED_CLS,
                                    1, 65536)
    if err != nil {
        fmt.Println("Failed to load ingress func: %v\n", err)
        return nil, err
    }
    fmt.Println("Loaded Ingress func to structure")

    egress_fn, err := bpf_mod.Load("handle_egress",
                                   C.BPF_PROG_TYPE_SCHED_CLS,
                                   1, 65536)
    if err != nil {
        fmt.Println("Failed to load egress func: %v\n", err)
        return nil, err
    }

    fmt.Println("Loaded Egress func to structure")

    traffic_table := bcc.NewTable(bpf_mod.TableId("dports2proto"), bpf_mod)
    if err := setTrafficTable(traffic_table, int(monitoring_info.port_num),
                              monitoring_info.protocol, true);
        err != nil {
        fmt.Printf("Error on setting traffic port")
        return nil, err
    }

    egress_match_list := get_egress_match_list(pod_name)

    egress_table := bcc.NewTable(bpf_mod.TableId("egress_lookup_table"), bpf_mod)
    if egress_match_list != nil {
        if err := setEgressTable(egress_table, egress_match_list, 1, true); err != nil {
            return nil, err
        }
    }

    session_table := bcc.NewTable(bpf_mod.TableId("sessions"), bpf_mod)

    attrs := netlink.QdiscAttrs {
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
        return nil, err
    }

    fmt.Printf("Qdisc for clsact added for index %v\n", ifindex)

    ingress_filter_attrs := netlink.FilterAttrs{
        LinkIndex:  ifindex,
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
        return nil, err
    }

    if err := netlink.FilterAdd(ingress_filter); err != nil {
        fmt.Println(err)
        return nil, err
    }

    egress_filter_attrs := netlink.FilterAttrs{
        LinkIndex:  ifindex,
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
        return nil, err
    }

    if err := netlink.FilterAdd(egress_filter); err != nil {
        fmt.Println(err)
        return nil, err
    }

    table := bcc.NewTable(bpf_mod.TableId("skb_events"), bpf_mod)

    skb_rev_chan := make(chan []byte)

    perfMap, err := bcc.InitPerfMap(table, skb_rev_chan)
    if err != nil {
        fmt.Println(err)
        return nil, err
    }

    tracer, closer := initJaeger(monitoring_info.svc_name)
    ticker := time.NewTicker(500 * time.Millisecond)
    stop := make(chan bool)
    go func() {
        for {
            select {
                case <- ticker.C:
                    print_network_traces(tracer)
                case data := <-skb_rev_chan:
                    err = handle_skb_event(&data, node_name, pod_name, session_table,
                                           monitoring_info, egress_match_list)
                    if err != nil {
                        fmt.Printf("failed to decode received data: %s\n", err)
                    }
                case <- stop:
                    fmt.Printf("Receiving stop for pod %v\n", pod_name)
                    ticker.Stop()
                    perfMap.Stop()
                    closer.Close()
                    // TODO(s3wong): uncomment remove qdisc del once k8s watcher implemented
                    //netlink.QdiscDel(qdisc)
                    bpf_mod.Close()
                    return
            }
        }
    }()

    perfMap.Start()
    return &ClovisorBCC{
        stopChan:   stop,
        qdisc:      qdisc,
    }, nil
}

func (clovBcc *ClovisorBCC) StopPod() {
    // TODO(s3wong): remove qdisc del once k8s watcher implemented
    netlink.QdiscDel(clovBcc.qdisc)
    clovBcc.stopChan <- true
}
