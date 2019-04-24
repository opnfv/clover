// Copyright (c) Authors of Clover
//
// All rights reserved. This program and the accompanying materials
// are made available under the terms of the Apache License, Version 2.0
// which accompanies this distribution, and is available at
// http://www.apache.org/licenses/LICENSE-2.0

package clovisor

import (
    "encoding/hex"
    //"encoding/json"
    "bytes"
    "encoding/binary"
    "errors"
    "fmt"
    "io/ioutil"
    "net"
    //"net/http"
    "plugin"
    "strconv"
    "strings"
    "time"

    //"github.com/go-redis/redis"
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
#include <bcc/bcc_common.h>
#include <bcc/libbpf.h>
*/
import "C"

type Parser interface {
    Parse(session_key string, is_req bool, data []byte)([]byte, map[string]string)
}

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
    done        bool
    service     string
    generalInfo map[string]string
    traces      []map[string]string
    reqBuf      []byte
    respBuf     []byte
}

const (
    HTTP = 1 << iota
    HTTP2 = 1 << iota
    TCP = 1 << iota
    UDP = 1 << iota
)

//var sessionMap map[string]map[string]string;
var sessionMap map[string]*session_info_t;
var protocolParser = map[string]Parser{};
var defaultModPath = map[string]string{
    "http":     "/proto/http.so",
}
var tracerMap = map[string]opentracing.Tracer{};

var veth_ifidx_command = "cat /sys/class/net/eth0/iflink";

var protocolMap = map[string]int{
    "http":     1,
    "http2":    2,
    "tcp":      3,
    "udp":      4,
}

var traceTable string = "NetworkTraces"

/*
 * redisConnect: redis client connecting to redis server
func redisConnect() *redis.Client {
    client := redis.NewClient(&redis.Options{
        Addr:       fmt.Sprintf("%s:6379", redisServer),
        Password:   "",
        DB:         0,
    })
    return client
}
 */

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

func loadProtoParser(protocol string, update bool) error {
    var modPath = ""

    if !update {
        if _, ok := protocolParser[protocol]; ok {
            fmt.Printf("Found parse function for protocol %s\n", protocol)
            return nil
        }
    }

    client := redisConnect()

    redisResult := client.HGet(ProtoCfg, protocol)
    if redisResult.Err() == nil {
        if len(redisResult.Val()) > 0 {
            modPath = redisResult.Val()
        }
    }
    if len(modPath) == 0 {
        if _, ok := defaultModPath[protocol]; ok {
            modPath = defaultModPath[protocol]
        } else {
            return errors.New(fmt.Sprintf("Unable to find module path for protocol %s", protocol))
        }
    }

    fmt.Printf("Loading plugin for protocol %v with %v\n", protocol, modPath)

    plug, err := plugin.Open(modPath)
    if err != nil {
        fmt.Println(err)
        return err
    }

    symParse, err := plug.Lookup("Parser")
    if err != nil {
        fmt.Println(err)
        return err
    }

    var parser Parser
    parser, ok := symParse.(Parser)
    if !ok {
        fmt.Printf("Unexpected type from mod %s symbol parse\n", modPath)
        return errors.New(fmt.Sprintf("Wrong type for func parse from %s", modPath))
    }

    protocolParser[protocol] = parser
    return nil
}

func print_network_traces() {
    /*
    client := redisConnect()

    traces, err := client.HGetAll(traceTable).Result()
    if err != nil {
        fmt.Printf("Error retriving traces from redis: %v\n", err.Error())
        return
    }
    */
    /*
        structure:
        "done": "true",
        "traces": array of protocol traces
                  [0] : "admin": map[string]string
                  [1] : "ipv4 or ipv6": map[string]string
                  [2] : "tcp or udp": map[string]string
                  [3] : "http"...
     */
     /*
    for key, value := range traces {
        traceMap := map[string]interface{}
        json.Unmarshal([]byte(value), &traceMap)
        if _, ok := traceMap["done"]; ok {
            span := tracer.StartSpan(fmt.Sprintf("tracing-%s", key))
            for idx, trace := range traceMap["traces"] {
                span.SetTag(fmt.Sprintf("protocol-%d", idx), trace['protocol'])
                for tag, tagVal := range trace {
                    if tag == "protocol" {
                        continue
                    }
                    span.SetTag(tag, tagVal)
                }
            }
            span.Finish()
            ret := client.HDel(traceTable, key)
            if ret.Err() != nil {
                fmt.Printf("Error deleting %v from %v: %v\n", key, traceTable, ret.Err())
            }
        }
    }
    */
    for key, value := range sessionMap {
        if value.done {
            tracer := tracerMap[value.service]
            span := tracer.StartSpan(fmt.Sprintf("tracing-%s", key))
            for genTag, genVal := range value.generalInfo {
                fmt.Printf("general info writing %v: %v\n", genTag, genVal)
                span.SetTag(genTag, genVal)
            }
            for idx, trace := range value.traces {
                span.SetTag(fmt.Sprintf("protocol-%d", idx), trace["protocol"])
                for tag, tagVal := range trace {
                    if tag == "protocol" {
                        continue
                    }
                    fmt.Printf("%v writing %v: %v\n", trace["protocol"], tag, tagVal)
                    span.SetTag(tag, tagVal)
                }
            }
            span.Finish()
            delete(sessionMap, key)
        }
    }
}

func handle_skb_event(data *[]byte, node_name string, pod_name string,
                      session_table *bcc.Table,
                      monitoring_info *monitoring_info_t,
                      egress_match_list []egress_match_t,
                      svc_name string) (error) {
    //fmt.Printf("monitoring info has %v\n", monitoring_info)
    fmt.Printf("\n\nnode[%s] pod[%s]\n%s\n", node_name, pod_name, hex.Dump(*data))
    var ipproto layers.IPProtocol
    var src_ip, dst_ip uint32
    var src_port, dst_port uint16
    var session_key, src_ip_str, dst_ip_str string
    is_req := false
    proto := HTTP
    is_ingress:= binary.LittleEndian.Uint32((*data)[0:4])
    packet := gopacket.NewPacket((*data)[4:len(*data)],
                                 layers.LayerTypeEthernet,
                                 gopacket.Default)
    if ipv4_layer := packet.Layer(layers.LayerTypeIPv4); ipv4_layer != nil {
        ipv4, _ := ipv4_layer.(*layers.IPv4)
        src_ip_str = ipv4.SrcIP.String()
        dst_ip_str = ipv4.DstIP.String()
        ipproto = ipv4.Protocol
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
    if dst_port == uint16(monitoring_info.port_num) || egress_port_req {
        is_req = true
    }
    if is_req {
        session_key = fmt.Sprintf("%x:%x:%d:%d:%d", src_ip, dst_ip, ipproto,
                                  src_port, dst_port)
    } else {
        session_key = fmt.Sprintf("%x:%x:%d:%d:%d", dst_ip, src_ip, ipproto,
                                  dst_port, src_port)
    }
    var sess_map *session_info_t
    if _, ok := sessionMap[session_key]; !ok {
        sess_map = &session_info_t{}
        sess_map.done = false
        sess_map.service = svc_name
        sess_map.generalInfo = make(map[string]string)
        sess_map.traces = []map[string]string{}
        sess_map.reqBuf = []byte{}
        sess_map.respBuf = []byte{}
        sessionMap[session_key] = sess_map
        zero := strconv.Itoa(0)
        sessionMap[session_key].generalInfo["reqpakcount"] = zero
        sessionMap[session_key].generalInfo["reqbytecount"] = zero
        sessionMap[session_key].generalInfo["resppakcount"] = zero
        sessionMap[session_key].generalInfo["respbytecount"] = zero
        sessionMap[session_key].generalInfo["nodename"] = node_name
        sessionMap[session_key].generalInfo["podname"] = pod_name
    } else {
        sess_map = sessionMap[session_key]
    }

    curr_pak_count := 0
    curr_byte_count := 0
    map_val := sess_map.generalInfo
    if is_req {
        curr_pak_count, _ = strconv.Atoi(map_val["reqpakcount"])
        curr_byte_count, _ = strconv.Atoi(map_val["reqbytecount"])
    } else {
        curr_pak_count, _ = strconv.Atoi(map_val["resppakcount"])
        curr_byte_count, _ = strconv.Atoi(map_val["respbytecount"])
    }
    curr_pak_count++
    curr_byte_count += len(packet.Data())
    if is_req {
        map_val["reqpakcount"] = strconv.Itoa(curr_pak_count)
        map_val["reqbytecount"] = strconv.Itoa(curr_byte_count)
    } else {
        map_val["resppakcount"] = strconv.Itoa(curr_pak_count)
        map_val["respbytecount"] = strconv.Itoa(curr_byte_count)
    }

    if is_req {
        // TODO (s3wong): just do IPv4 and TCP without using the plugin for now
        // the condition check itself is cheating also...
        if len(sess_map.traces) <= 1 {
            ipv4Map := make(map[string]string)
            ipv4Map["protocol"] = "IPv4"
            ipv4Map["srcip"] = src_ip_str
            ipv4Map["dstip"] = dst_ip_str
            sess_map.traces = append(sess_map.traces, ipv4Map)
            tcpMap := make(map[string]string)
            tcpMap["protocol"] = "TCP"
            tcpMap["srcport"] = fmt.Sprintf("%d", src_port)
            tcpMap["dstport"] = fmt.Sprintf("%d", dst_port)
            sess_map.traces = append(sess_map.traces, tcpMap)
        }
    }

    var dataptr []byte
    app_layer := packet.ApplicationLayer()
    errStr := ""
    if app_layer != nil {
        if is_req {
            dataptr = append(sess_map.reqBuf, app_layer.Payload()...)
        } else {
            dataptr = append(sess_map.respBuf, app_layer.Payload()...)
        }
        for _, protocol := range monitoring_info.protocols {
            if _, ok := protocolParser[protocol]; ok {
                parser := protocolParser[protocol]
                new_dataptr, parseMap := parser.Parse(session_key, is_req,
                                                      dataptr)
                if parseMap != nil {
                    protocolTag := strings.ToUpper(protocol)
                    merged := false
                    for _, existing := range sess_map.traces {
                        if existing["protocol"] == protocolTag {
                            for k, v := range parseMap {
                                existing[k] = v
                            }
                            merged = true
                            break
                        }
                    }
                    if !merged {
                        parseMap["protocol"] = strings.ToUpper(protocol)
                        sess_map.traces = append(sess_map.traces, parseMap)
                    }
                    dataptr = new_dataptr
                } else {
                    // offset to packet is off, no need to continue
                    // parsing, return error
                    errStr = fmt.Sprintf("Error: unable to parse protocol %v", protocol)
                    fmt.Println(errStr)
                    //return errors.New(errStr)
                    break
                }
            }
        }
    } else {
        fmt.Printf("No application layer, TCP packet\n")
        return nil
    }

    if len(errStr) > 0 {
        // buffer
        if is_req {
            sess_map.reqBuf = append([]byte(nil), dataptr...)
        } else {
            sess_map.respBuf = append([]byte(nil), dataptr...)
        }
        //sessionMap[session_key] = sess_map
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
                fmt.Println("Error: unable to allocate new byte buffer")
                return nil
            }
            session := session_t{}
            if err = binary.Read(leaf_buf, binary.LittleEndian, &session);
                err != nil {
                fmt.Println(err)
                return nil
            }
            if session.Resp_time == 0 {
                fmt.Printf("session response time not set yet\n")
            } else {
                duration = (session.Resp_time - session.Req_time)/1000
                fmt.Printf("session time : %v\n", session)
                fmt.Printf("Duration: %d usec\n", duration)
            }
            map_val["duration"] = fmt.Sprintf("%v usec", duration)

            node, node_session, err := getNodeIntfSession(session_key)
            if err == nil {
                map_val["node-interface"] = node
                map_val["node-request-ts"] = fmt.Sprintf("%v", node_session.Req_time)
                map_val["node-response-ts"] = fmt.Sprintf("%v", node_session.Resp_time)
                delNodeIntfSession(node, key)
            } else {
                fmt.Printf("Session not found in any node interface... posssibly local?")
            }

            if duration > 0 {
                sess_map.done = true
                err := session_table.Delete(key)
                if err != nil {
                    fmt.Printf("Error deleting key %v: %v\n", key, err)
                    return err
                }
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

var nodeintfFilterList = [...]string {"lo", "veth", "docker", "flannel"}

func filterNodeIntf(intf string) bool {
    for _, substring := range nodeintfFilterList {
        if strings.Contains(intf, substring) {
            return false
        }
    }
    return true
}

type nodeIntf struct {
    bpfMod          *bcc.Module
    ipTrackTable    *bcc.Table
    sessionTable    *bcc.Table
}

var nodeIntfMap = map[string]*nodeIntf{}

func setupNodeIntf(ifindex int) (*nodeIntf, error) {
    buf, err := ioutil.ReadFile("libclovisor/ebpf/node_interface.c")
    if err != nil {
        fmt.Println(err)
        return nil, err
    }
    code := string(buf)

    bpf_mod := bcc.NewModule(code, []string{})

    ingress_fn, err := bpf_mod.Load("handle_ingress",
                                    C.BPF_PROG_TYPE_SCHED_CLS,
                                    1, 65536)
    if err != nil {
        fmt.Printf("Failed to load node interface ingress func: %v\n", err)
        return nil, err
    }

    egress_fn, err := bpf_mod.Load("handle_egress",
                                   C.BPF_PROG_TYPE_SCHED_CLS,
                                   1, 65536)
    if err != nil {
        fmt.Printf("Failed to load node interface egress func: %v\n", err)
        return nil, err
    }

    ip_track_table := bcc.NewTable(bpf_mod.TableId("ip2track"), bpf_mod)
    node_sess_table := bcc.NewTable(bpf_mod.TableId("node_sessions"), bpf_mod)

    // check if qdisc clsact filter for this interface already exists
    link, err := netlink.LinkByIndex(ifindex)
    if err != nil {
        fmt.Println(err)
    } else {
        qdiscs, err := netlink.QdiscList(link)
        if err == nil {
            for _, qdisc_ := range qdiscs {
                if qdisc_.Type() == "clsact" {
                    netlink.QdiscDel(qdisc_)
                    break
                }
            }
        }
    }

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
        fmt.Println("Failed to load node interface ingress bpf program")
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
        fmt.Println("Failed to load node interface egress bpf program")
        return nil, err
    }

    if err := netlink.FilterAdd(egress_filter); err != nil {
        fmt.Println(err)
        return nil, err
    }

    ip_track_table.DeleteAll()
    node_sess_table.DeleteAll()

    return &nodeIntf{
        bpfMod:         bpf_mod,
        ipTrackTable:   ip_track_table,
        sessionTable:   node_sess_table,
    }, nil
}

func ClovisorPhyInfSetup() error {
    intfList, err := net.Interfaces()
    if err != nil {
        fmt.Printf("Failed to get node interfaces: %v\n", err)
        return err
    }

    for _, f := range intfList {
        if !filterNodeIntf(f.Name) {
            continue
        }
        fmt.Printf("Tracking node interface %v w/ index %v\n", f.Name, f.Index)
        bpf_node_intf, err := setupNodeIntf(f.Index)
        if err != nil {
            fmt.Printf("Failed to set up node interface %v: %v\n", f.Name, err)
            return err
        }
        nodeIntfMap[f.Name] = bpf_node_intf
    }
    return nil
}

func setIPTrackingTable(table *bcc.Table, ipaddr uint32, action int) error {
    key, _ := table.KeyStrToBytes(strconv.Itoa(int(ipaddr)))
    leaf, _ := table.LeafStrToBytes(strconv.Itoa(action))
    if err := table.Set(key, leaf); err != nil {
        fmt.Printf("Failed to set IP tracking table: %v\n", err)
        return err
    }
    dumpBPFTable(table)
    return nil
}

func setNodeIntfTrackingIP(ipaddr uint32) {
    for name, node_intf := range nodeIntfMap {
        err := setIPTrackingTable(node_intf.ipTrackTable, ipaddr, 1)
        if err != nil {
            fmt.Printf("Failed to add ip address %v to node interface %v: %v\n", backtoIP4(int64(ipaddr)), name, err)
        }
    }
}

func getNodeIntfSession(session_key session_key_t) (string, *session_t, error) {
    key_buf := &bytes.Buffer{}
    binary.Write(key_buf, binary.LittleEndian, session_key)
    key := append([]byte(nil), key_buf.Bytes()...)

    for node, node_intf := range nodeIntfMap {
        fmt.Printf("For node interface %v... ", node)
        //dumpBPFTable(node_intf.sessionTable)
        if leaf, err := node_intf.sessionTable.Get(key); err == nil {
            leaf_buf := bytes.NewBuffer(leaf)
            session := session_t{}
            binary.Read(leaf_buf, binary.LittleEndian, &session)
            return node, &session, nil
        }
    }
    return "", nil, errors.New("session not found")
}

func delNodeIntfSession(node_iname string, key []byte) error {
    nodeIntf := nodeIntfMap[node_iname]
    err := nodeIntf.sessionTable.Delete(key)
    if err != nil {
        fmt.Printf("Error deleting session %v from node interface %v: %v\n",
                   key, node_iname, err)
    }
    return err
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

    sessionMap = map[string]*session_info_t{};

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
                              monitoring_info.protocols[0], true);
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

    // check if qdisc clsact filter for this interface already exists
    link, err := netlink.LinkByIndex(ifindex)
    if err != nil {
        fmt.Println(err)
    } else {
        qdiscs, err := netlink.QdiscList(link)
        if err == nil {
            for _, qdisc := range qdiscs {
                if qdisc.Type() == "clsact" {
                    netlink.QdiscDel(qdisc)
                    break
                }
            }
        }
    }

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

    setNodeIntfTrackingIP(ip2Long(monitoring_info.pod_ip))

    table := bcc.NewTable(bpf_mod.TableId("skb_events"), bpf_mod)

    skb_rev_chan := make(chan []byte)

    perfMap, err := bcc.InitPerfMap(table, skb_rev_chan)
    if err != nil {
        fmt.Println(err)
        return nil, err
    }

    stop := make(chan bool)
    go func() {
        fmt.Printf("Start tracing to Jaeger with service %v\n", monitoring_info.svc_name)
        tracer, closer := initJaeger(monitoring_info.svc_name)
        tracerMap[monitoring_info.svc_name] = tracer
        ticker := time.NewTicker(500 * time.Millisecond)
        for {
            select {
                case <- ticker.C:
                    print_network_traces()
                case data := <-skb_rev_chan:
                    err = handle_skb_event(&data, node_name, pod_name, session_table,
                                           monitoring_info, egress_match_list,
                                           monitoring_info.svc_name)
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
