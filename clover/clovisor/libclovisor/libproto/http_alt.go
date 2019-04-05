// Copyright (c) Authors of Clover
//
// All rights reserved. This program and the accompanying materials
// are made available under the terms of the Apache License, Version 2.0
// which accompanies this distribution, and is available at
// http://www.apache.org/licenses/LICENSE-2.0

package main

import (
    "bufio"
    "bytes"
    "fmt"
    "io/ioutil"
    "net/http"
)

type httpparser string

func (p httpparser) Parse(session_key string,
                          is_req bool,
                          data []byte) ([]byte, map[string]string) {
    map_val := make(map[string]string)
    reader := bytes.NewReader(data)
    buf := bufio.NewReader(reader)
    if is_req == true {
        req, err := http.ReadRequest(buf)
        if err != nil {
            fmt.Printf("Request error: ")
            fmt.Println(err)
            return nil, nil
        } else if req == nil {
            fmt.Println("request is nil")
            return nil, nil
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
            body, err := ioutil.ReadAll(req.Body)
            if err != nil {
                fmt.Printf("Error reading HTTP Request body %v\n", err.Error())
            }
            return body, map_val
        }
    } else {
        // response
        resp, err := http.ReadResponse(buf, nil)
        if err != nil {
            fmt.Printf("Response error: ")
            fmt.Println(err)
            return nil, nil
        }
        fmt.Printf("HTTP Response Status %v code %v Proto %v\n",
                    resp.Status, resp.StatusCode, resp.Proto)
        map_val["respstatus"] = resp.Status
        map_val["respstatuscode"] = fmt.Sprintf("%v", resp.StatusCode)
        map_val["respproto"] = fmt.Sprintf("%v", resp.Proto)
        header := resp.Header
        //fmt.Printf("Response Header contains %v\n", header)
        if contentType := header.Get("Content-Type"); len(contentType) > 0 {
            map_val["content-type"] = contentType
        }
        if lastMod := header.Get("Last-Modified"); len(lastMod) > 0 {
            map_val["last-modified"] = lastMod
        }

        body, err := ioutil.ReadAll(resp.Body)
        if err != nil {
            fmt.Printf("Error reading HTTP Request body %v\n", err.Error())
        }
        return body, map_val
    }
}

var Parser httpparser
