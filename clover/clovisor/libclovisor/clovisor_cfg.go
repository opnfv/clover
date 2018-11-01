// Copyright (c) Authors of Clover
//
// All rights reserved. This program and the accompanying materials
// are made available under the terms of the Apache License, Version 2.0
// which accompanies this distribution, and is available at
// http://www.apache.org/licenses/LICENSE-2.0

package clovisor

import (
    "bytes"
    "encoding/binary"
    "fmt"
    "io"
    "net"
    "strconv"
    "strings"

    "github.com/go-redis/redis"
    opentracing "github.com/opentracing/opentracing-go"
    jaeger "github.com/uber/jaeger-client-go"
    jaeger_config "github.com/uber/jaeger-client-go/config"
)

var redisServer string = "redis.clover-system"
var jaegerCollector string = "jaeger-collector.clover-system:14268"
var jaegerAgent string = "jaeger-agent.clover-system:6831"

/*
 * redisConnect: redis client connecting to redis server
 */
func redisConnect() *redis.Client {
    client := redis.NewClient(&redis.Options{
        Addr:       fmt.Sprintf("%s:6379", redisServer),
        Password:   "",
        DB:         0,
    })
    return client
}

func get_cfg_labels(node_name string) ([]string, error) {
    client := redisConnect()
    labels_list, err := client.LRange("clovisor_labels", 0, -1).Result()
    if err != nil {
        fmt.Println(err.Error())
        return nil, err
    }

    return labels_list, err
}

func get_egress_match_list(pod_name string) ([]egress_match_t) {
    client := redisConnect()
    egress_cfg_list, err := client.LRange("clovior_egress_match", 0, -1).Result()
    if err != nil {
        fmt.Println(err.Error())
        return nil
    }
    ret_list := make([]egress_match_t, 0, len(egress_cfg_list))
    for _, em_cfg_str := range(egress_cfg_list) {
        fmt.Printf("egress match cfg == %v\n", em_cfg_str)
        em_cfg_slice := strings.Split(em_cfg_str, ":")
        if len(em_cfg_slice) < 2 {
            fmt.Printf("egress match config requires at least two fields [%v]\n", em_cfg_slice)
            continue
        } else if len(em_cfg_slice) == 3 {
            if strings.Contains(pod_name, em_cfg_slice[2]) {
                fmt.Printf("%v != %v, filtering out this config for pod %v\n",
                           em_cfg_slice[2], pod_name, pod_name)
                continue
            }
        }
        var ip uint32 = 0
        if em_cfg_slice[0] != "0" {
            ip = ip2Long(em_cfg_slice[0])
        }
        port_32, _ := strconv.Atoi(em_cfg_slice[1])
        port := uint16(port_32)
        ret_list = append(ret_list,  egress_match_t{ip, port})
    }
    return ret_list
}

// following function comes from
// https://www.socketloop.com/tutorials/golang-convert-ip-address-string-to-long-unsigned-32-bit-integer
func ip2Long(ip string) uint32 {
    var long uint32
    binary.Read(bytes.NewBuffer(net.ParseIP(ip).To4()), binary.LittleEndian, &long)
    return long
}

func get_cfg_session_match() ([]egress_match_cfg, error) {
    var ret_list []egress_match_cfg
    client := redisConnect()
    keys, err := client.HKeys("clovisor_session_match").Result()
    if err != nil {
        fmt.Println(err.Error())
        return nil, err
    }
    for _, key := range keys {
        value, err := client.HGet("clovisor_session_match", key).Result()
        if err != nil {
            fmt.Println(err.Error())
            continue
        }
        match_slice := strings.Split(key, "-")
        dst_ip := ip2Long(match_slice[0])
        dst_port, _ := strconv.Atoi(match_slice[1])
        egress_match := egress_match_t{
                dst_ip:     dst_ip,
                dst_port:   uint16(dst_port),
        }
        // organize into internally understandable struct
        ret_list = append(ret_list, egress_match_cfg{
                                        egress_match:   egress_match,
                                        action:         value,
                                    })
    }
    return ret_list, nil
}

func initJaeger(service string) (opentracing.Tracer, io.Closer) {
    cfg := &jaeger_config.Configuration{
        Sampler: &jaeger_config.SamplerConfig{
            Type:  "const",
            Param: 1,
        },
        Reporter: &jaeger_config.ReporterConfig{
            LogSpans: true,
            CollectorEndpoint: fmt.Sprintf("http://%s/api/traces", jaegerCollector),
            LocalAgentHostPort: fmt.Sprintf("%s", jaegerAgent),
        },
    }
    tracer, closer, err := cfg.New(service, jaeger_config.Logger(jaeger.StdLogger))
    if err != nil {
        panic(fmt.Sprintf("ERROR: cannot init Jaeger: %v\n", err))
    }
    return tracer, closer
}

func get_jaeger_server() (string, error) {
    client := redisConnect()
    return client.Get("clovisor_jaeger_server").Result()
}
