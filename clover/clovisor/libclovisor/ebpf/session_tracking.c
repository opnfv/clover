// Copyright (c) Authors of Clover
//
// All rights reserved. This program and the accompanying materials
// are made available under the terms of the Apache License, Version 2.0
// which accompanies this distribution, and is available at
// http://www.apache.org/licenses/LICENSE-2.0
#include <uapi/linux/if_ether.h>
#include <uapi/linux/in.h>
#include <uapi/linux/ip.h>
#include <uapi/linux/tcp.h>
#include <uapi/linux/pkt_cls.h>
#include <uapi/linux/bpf.h>

#include <bcc/proto.h>

#define HTTP_HDR_MIN_LEN 7
#define MAX_SESSION_TABLE_ENTRIES 8192

typedef enum {
    UNDEFINED = 0,
    HTTP = 1,
    HTTP2 = 2,
    TCP = 3,
    UDP = 4,
} app_proto_t;

typedef struct session_key_ {
    u32 src_ip;
    u32 dst_ip;
    unsigned short src_port;
    unsigned short dst_port;
} session_key_t;

typedef struct session_ {
    u64 req_time;
    u64 resp_time;
} session_t;

typedef struct egress_match_ {
    u32 dst_ip;
    unsigned short dst_port;
} egress_match_t;

typedef enum policy_action_ {
    RECORD = 1,
} policy_action_t;

BPF_PERF_OUTPUT(skb_events);
BPF_HASH(dports2proto, u16, u32);
BPF_HASH(egress_lookup_table, egress_match_t, policy_action_t);
BPF_HASH(sessions, session_key_t, session_t, MAX_SESSION_TABLE_ENTRIES);

struct eth_hdr {
	unsigned char   h_dest[ETH_ALEN];
	unsigned char   h_source[ETH_ALEN];
	unsigned short  h_proto;
};

static inline int ipv4_hdrlen(struct iphdr *ip4)
{
    return ip4->ihl * 4;
}

static inline int tcp_doff(struct tcphdr *tcp_hdr)
{
    return tcp_hdr->doff * 4;
}

static inline int http_parsing(void *data, void *data_end)
{

    int is_http = 1;
    if (data + HTTP_HDR_MIN_LEN > data_end) {
        bpf_trace_printk("No HTTP Header in TCP segment");
        return 0;
    }
    if (strncmp((char*)data, "HTTP", 4)) {
        if (strncmp((char*)data, "GET", 3)) {
            if (strncmp((char*)data, "POST", 4)) {
                if (strncmp((char*)data, "PUT", 3)) {
                    if (strncmp((char*)data, "HEAD", 4)) {
                        is_http = 0;
                    }
                }
            }
        }
    }
    return is_http;
}

static inline void fill_up_sess_key(session_key_t *key, u32 src_ip,
                                    u32 dst_ip, u16 src_port, u16 dst_port)
{
    key->src_ip = src_ip;
    key->dst_ip = dst_ip;
    key->src_port = src_port;
    key->dst_port = dst_port;
}

static inline int process_response(u32 src_ip, u32 dst_ip, u16 src_port,
                                   u16 dst_port)
{
    session_key_t sess_key = {};
    session_t *session_ptr = NULL;
    fill_up_sess_key(&sess_key, src_ip, dst_ip, src_port, dst_port);
    session_ptr = sessions.lookup(&sess_key);
    if (session_ptr != NULL) {
        u64 resp_time = bpf_ktime_get_ns();
        session_t update_session = {
            session_ptr->req_time,
            resp_time
        };
        sessions.update(&sess_key, &update_session);
        return 1;
    }
    return 0;
}

static inline void process_request(u32 src_ip, u32 dst_ip, u16 src_port,
                                   u16 dst_port)
{
    session_key_t sess_key = {};
    session_t *session_ptr = NULL;
    session_t new_session = {
        bpf_ktime_get_ns(),
        0
    };
    fill_up_sess_key(&sess_key, src_ip, dst_ip, src_port, dst_port);
    session_ptr = sessions.lookup(&sess_key);
    if (! session_ptr) {
        sessions.insert(&sess_key, &new_session);
    }
    /*
    if (session_ptr != NULL) {
        sessions.update(&sess_key, &new_session);
    } else {
        sessions.insert(&sess_key, &new_session);
    }
    */
}

static inline app_proto_t ingress_tcp_parsing(struct tcphdr *tcp_hdr,
                                              struct iphdr *ipv4_hdr,
                                              void *data_end)
{
    unsigned short dest_port = htons(tcp_hdr->dest);
    egress_match_t egress_match = {};
    policy_action_t *policy_ptr = NULL;
    app_proto_t ret = TCP;

    unsigned int *proto = dports2proto.lookup(&dest_port);
    if (proto != NULL) {
        /*
        if (tcp_hdr->syn && !tcp_hdr->ack) {
            return ret;
        }
        */
        ret = HTTP;
        if (tcp_hdr->fin || tcp_hdr->rst) {
            process_response(ntohl(ipv4_hdr->saddr),
                             ntohl(ipv4_hdr->daddr),
                             ntohs(tcp_hdr->source),
                             ntohs(tcp_hdr->dest));
        } else {
            process_request(ntohl(ipv4_hdr->saddr),
                            ntohl(ipv4_hdr->daddr),
                            ntohs(tcp_hdr->source),
                            ntohs(tcp_hdr->dest));
        }
    } else {
        dest_port = htons(tcp_hdr->source);
        proto = dports2proto.lookup(&dest_port);
        if (proto != NULL) {
            // clock response receiving time
            process_response(ntohl(ipv4_hdr->daddr),
                             ntohl(ipv4_hdr->saddr),
                             ntohs(tcp_hdr->dest),
                             ntohs(tcp_hdr->source));
        }
        egress_match.dst_ip = ntohl(ipv4_hdr->saddr);
        egress_match.dst_port = ntohs(tcp_hdr->source);
        policy_ptr = egress_lookup_table.lookup(&egress_match);
        if (policy_ptr == NULL) {
            egress_match.dst_ip = 0;
            policy_ptr = egress_lookup_table.lookup(&egress_match);
        }

        if (policy_ptr != NULL) {
            if (*policy_ptr == RECORD) {
                ret = HTTP;
                if (tcp_hdr->fin || tcp_hdr->rst) {
                    process_response(ntohl(ipv4_hdr->daddr),
                                     ntohl(ipv4_hdr->saddr),
                                     ntohs(tcp_hdr->dest),
                                     ntohs(tcp_hdr->source));
                }
            }
        }
    }

    // everything else drops to TCP
    //return ((void*)tcp_hdr);
    return ret;
}

static inline app_proto_t egress_tcp_parsing(struct tcphdr *tcp_hdr,
                                             struct iphdr *ipv4_hdr,
                                             void *data_end)
{
    unsigned short src_port = htons(tcp_hdr->source);
    app_proto_t ret = TCP;
    egress_match_t egress_match = {};
    policy_action_t *policy_ptr = NULL;

    unsigned int *proto = dports2proto.lookup(&src_port);

    if (proto != NULL) {
        //if (tcp_hdr->fin || tcp_hdr->rst) {
        process_response(ntohl(ipv4_hdr->daddr),
                         ntohl(ipv4_hdr->saddr),
                         ntohs(tcp_hdr->dest),
                         ntohs(tcp_hdr->source));
        //}
        ret = HTTP;
    } else {

        egress_match.dst_ip = ntohl(ipv4_hdr->daddr);
        egress_match.dst_port = ntohs(tcp_hdr->dest);
        policy_ptr = egress_lookup_table.lookup(&egress_match);
        if (policy_ptr == NULL) {
            egress_match.dst_ip = 0;
            policy_ptr = egress_lookup_table.lookup(&egress_match);
        }

        if (policy_ptr != NULL) {
            if (*policy_ptr == RECORD) {
                process_request(ntohl(ipv4_hdr->saddr),
                                ntohl(ipv4_hdr->daddr),
                                ntohs(tcp_hdr->source),
                                ntohs(tcp_hdr->dest));
                ret = HTTP;
            }
        }
    }
    //return(ret_hdr);
    return ret;
}

static inline int handle_packet(struct __sk_buff *skb, int is_ingress)
{
	void *data = (void *)(long)skb->data;
	void *data_end = (void *)(long)skb->data_end;
	struct eth_hdr *eth = data;
    struct iphdr *ipv4_hdr = data + sizeof(*eth);
    struct tcphdr *tcp_hdr = data + sizeof(*eth) + sizeof(*ipv4_hdr);
    app_proto_t proto = TCP;

    /* TODO(s3wong): assuming TCP only for now */
	/* single length check */
	if (data + sizeof(*eth) + sizeof(*ipv4_hdr) + sizeof(*tcp_hdr) > data_end)
		return TC_ACT_OK;

    if (eth->h_proto != htons(ETH_P_IP))
        return TC_ACT_OK;

    // TODO(s3wong): no support for IP options
    if (ipv4_hdr->protocol != IPPROTO_TCP || ipv4_hdr->ihl != 5)
        return TC_ACT_OK;

    if (is_ingress == 1) {
        proto = ingress_tcp_parsing(tcp_hdr, ipv4_hdr, data_end);
    } else{
        proto = egress_tcp_parsing(tcp_hdr, ipv4_hdr, data_end);
    }

	if (proto == HTTP) {
        int offset = is_ingress;
	    skb_events.perf_submit_skb(skb, skb->len, &offset, sizeof(offset));
    }

	return TC_ACT_OK;
}

int handle_ingress(struct __sk_buff *skb)
{
    return handle_packet(skb, 1);
}

int handle_egress(struct __sk_buff *skb)
{
    return handle_packet(skb, 0);
}
