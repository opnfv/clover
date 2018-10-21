# Copyright (c) Authors of Clover
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0

import redis
import logging

REDIS_HOST = 'redis.default'


class RedisOps:

    def __init__(self, host=REDIS_HOST):
        logging.basicConfig(filename='redisops.log',
                            level=logging.DEBUG)
        try:
            self.r = redis.StrictRedis(host=host, port=6379, db=0)
        except Exception as e:
            logging.debug(e)

    def init_services(self, skey='visibility_services'):
        service_names = ['http_lb', 'proxy_access_control']
        for s in service_names:
            self.r.sadd(skey, s)

    def set_tracing_services(self, services, skey='tracing_services'):
        self.r.delete(skey)
        for s in services:
            self.r.sadd(skey, s)

    def init_metrics(self, pkey='metric_prefixes', skey='metric_suffixes'):
        metric_prefixes = ['envoy_cluster_outbound_', 'envoy_cluster_inbound_']
        metric_suffixes = [
            '_default_svc_cluster_local_upstream_rq_2xx',
            '_default_svc_cluster_local_upstream_cx_active']
        for p in metric_prefixes:
            self.r.sadd(pkey, p)
        for s in metric_suffixes:
            self.r.sadd(skey, s)

    def get_services(self, skey='visibility_services'):
        services = self.r.smembers(skey)
        return services

    def get_metrics(self, pkey='metric_prefixes', skey='metric_suffixes'):
        prefixes = self.r.smembers(pkey)
        suffixes = self.r.smembers(skey)
        return prefixes, suffixes


def main():
    r = RedisOps()
    r.init_services()
    r.init_metrics()
    r.get_services()
    r.get_metrics()


if __name__ == '__main__':
    main()
