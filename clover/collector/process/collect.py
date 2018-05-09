# Copyright (c) Authors of Clover
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0

from clover.tracing.tracing import Tracing
from clover.monitoring.monitoring import Monitoring
from clover.collector.db.cassops import CassandraOps

# import pprint
import time
import argparse
import logging

TRACING_SERVICES = ['istio-ingress']
# TRACING_PORT = "16686"
TRACING_PORT = "30869"
MONITORING_PORT = "9090"
CASSANDRA_PORT = 9042  # Provide as integer
MONITORING_HOST = "10.244.0.198"
TRACING_HOST = "localhost"
CASSANDRA_HOSTS = ['172.17.0.3']


class Collector:

    def __init__(self, t_port, t_host, m_port, m_host, c_port, c_hosts):
        self.t = Tracing(t_host, t_port, '', False)
        monitoring_url = "http://{}:{}".format(m_host, m_port)
        self.m = Monitoring(monitoring_url)
        self.c = CassandraOps(c_hosts, c_port)
        logging.basicConfig(filename='collector.log', level=logging.DEBUG)

    # TODO configure time back and batch write to db
    def get_tracing(self, services):
        for service in services:
            traces = self.t.getTraces(service, 3600)
            try:
                self.set_tracing(traces)
            except Exception as e:
                logging.debug(e)

    # Insert to cassandra visibility traces and spans tables
    def set_tracing(self, trace):
        for traces in trace['data']:
            for spans in traces['spans']:
                    span = {}
                    span['spanID'] = spans['spanID']
                    span['duration'] = spans['duration']
                    span['startTime'] = spans['startTime']
                    span['operationName'] = spans['operationName']
                    tag = {}
                    for tags in spans['tags']:
                        tag[tags['key']] = tags['value']
                    self.c.insert_tracing('spans', traces['traceID'],
                                          span, tag)
            process_list = []
            for p in traces['processes']:
                process_list.append(p)
            service_names = []
            for pname in process_list:
                service_names.append(traces['processes'][pname]['serviceName'])
            self.c.insert_trace(traces['traceID'], service_names)

    # Insert to cassandra visibility metrics table
    def get_monitoring(self):

        # TODO add Redis interface to fetch collector metrics
        service_names = ['http_lb', 'proxy_access_control']
        metric_prefixes = ['envoy_cluster_out_', 'envoy_cluster_in_']
        metric_suffixes = [
            '_default_svc_cluster_local_http_internal_upstream_rq_2xx',
            '_default_svc_cluster_local_http_upstream_cx_active']

        for sname in service_names:
            for prefix in metric_prefixes:
                for suffix in metric_suffixes:
                    try:
                        metric_name = prefix + sname + suffix
                        query_params = {
                            "type": "instant",
                            "query": metric_name
                        }
                        data = self.m.query(query_params)
                        m_value = data['data']['result'][0]['value'][1]
                        m_time = data['data']['result'][0]['value'][0]
                        mn = data['data']['result'][0]['metric']['__name__']
                        self.c.insert_metric(mn, m_value, str(m_time), sname)
                    except Exception as e:
                        logging.debug(e)

        # TODO add batch retrieval for monitoring metrics
        # query_range_param = {
        #         "type": "range",
        #         "query": "tbd",
        #         "start": "60m",
        #         "end": "5m",
        #         "step": "30s"
        # }
        # data = self.m.query(query_range_param)
        # pp = pprint.PrettyPrinter(indent=2)
        # pp.pprint(data)


def main(args):
    c = Collector(args['t_port'], args['t_host'], args['m_port'],
                  args['m_host'], args['c_port'], args['c_hosts'])
    loop = True
    while loop:
        try:
            c.get_tracing(args['t_services'])
            c.get_monitoring()
            time.sleep(int(args['sinterval']))
        except KeyboardInterrupt:
            loop = False


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
            '-sinterval', default=5,
            help='Sample interval for collector loop')
    parser.add_argument(
            '-t_port', default=TRACING_PORT,
            help='Port to access Jaeger tracing')
    parser.add_argument(
            '-m_port', default=MONITORING_PORT,
            help='Port to access Prometheus monitoring')
    parser.add_argument(
            '-t_host', default=TRACING_HOST,
            help='Host to access Jaeger tracing')
    parser.add_argument(
            '-m_host', default=MONITORING_HOST,
            help='Host to access Prometheus monitoring')
    parser.add_argument(
            '-c_hosts', default=CASSANDRA_HOSTS,
            help='Host(s) to access Cassandra cluster')
    parser.add_argument(
            '-c_port', default=CASSANDRA_PORT,
            help='Port to access Cassandra cluster')
    parser.add_argument(
            '-t_services', default=TRACING_SERVICES,
            help='Collect services on this list of services')

    args, unknown = parser.parse_known_args(['&'])
    print(main(vars(args)))
