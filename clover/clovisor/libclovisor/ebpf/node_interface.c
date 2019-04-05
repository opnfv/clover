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

#define MAX_SESSION_TABLE_ENTRIES 8192

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

BPF_HASH(ip2track, u32, u32);
BPF_HASH(node_sessions, session_key_t, session_t, MAX_SESSION_TABLE_ENTRIES);

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

static inline void fill_up_sess_key(session_key_t *key, u32 src_ip,
                                    u32 dst_ip, u16 src_port, u16 dst_port)
{
    key->src_ip = src_ip;
    key->dst_ip = dst_ip;
    key->src_port = src_port;
    key->dst_port = dst_port;
}

static inline void process_response(u32 src_ip, u32 dst_ip, u16 src_port,
                                    u16 dst_port)
{
    session_key_t sess_key = {};
    session_t *session_ptr = NULL;
    fill_up_sess_key(&sess_key, src_ip, dst_ip, src_port, dst_port);
    session_ptr = node_sessions.lookup(&sess_key);
    if (session_ptr != NULL) {
        u64 resp_time = bpf_ktime_get_ns();
        session_t update_session = {
            session_ptr->req_time,
            resp_time
        };
        node_sessions.update(&sess_key, &update_session);
    }
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
    session_ptr = node_sessions.lookup(&sess_key);
    if (! session_ptr) {
        node_sessions.insert(&sess_key, &new_session);
    }
}

static inline void ingress_parsing(struct tcphdr *tcp_hdr,
                                   struct iphdr *ipv4_hdr)
{
    unsigned int dst_ip = ntohl(ipv4_hdr->daddr);
    int ret = 0;

    unsigned int *proto = ip2track.lookup(&dst_ip);
    if (proto != NULL) {
        process_response(ntohl(ipv4_hdr->daddr),
                         ntohl(ipv4_hdr->saddr),
                         ntohs(tcp_hdr->dest),
                         ntohs(tcp_hdr->source));
    }
}

static inline void egress_parsing(struct tcphdr *tcp_hdr,
                                  struct iphdr *ipv4_hdr)
{
    unsigned int src_ip = ntohl(ipv4_hdr->saddr);

    unsigned int *proto = ip2track.lookup(&src_ip);

    if (proto != NULL) {
        process_request(ntohl(ipv4_hdr->saddr),
                        ntohl(ipv4_hdr->daddr),
                        ntohs(tcp_hdr->source),
                        ntohs(tcp_hdr->dest));
    }
}

static inline int handle_packet(struct __sk_buff *skb, int is_ingress)
{
	void *data = (void *)(long)skb->data;
	void *data_end = (void *)(long)skb->data_end;
	struct eth_hdr *eth = data;
    struct iphdr *ipv4_hdr = data + sizeof(*eth);
    struct tcphdr *tcp_hdr = data + sizeof(*eth) + sizeof(*ipv4_hdr);

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
        ingress_parsing(tcp_hdr, ipv4_hdr);
    } else{
        egress_parsing(tcp_hdr, ipv4_hdr);
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
