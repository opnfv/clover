# Copyright (c) Authors of Clover
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0

from clover.tracing.tracing import Tracing
from clover.monitoring.monitoring import Monitoring
from clover.collector.db.cassops import CassandraOps
from clover.collector.db.redisops import RedisOps

# import pprint
import time
import argparse
import logging
import ast

TRACING_PORT = "16686"
MONITORING_PORT = "9090"
CASSANDRA_PORT = 9042  # Provide as integer
MONITORING_HOST = "prometheus.istio-system"
TRACING_HOST = "tracing.istio-system"
CASSANDRA_HOSTS = ['cassandra.clover-system']


class Collector:

    def __init__(self, t_port, t_host, m_port, m_host, c_port, c_hosts):

        # logging.basicConfig(filename='collector.log', level=logging.DEBUG)
        logging.basicConfig(filename='collector.log', level=logging.ERROR)
        # logging.getLogger("requests").setLevel(logging.DEBUG)
        logging.getLogger("requests").setLevel(logging.ERROR)
        # logging.getLogger("urllib3").setLevel(logging.DEBUG)
        logging.getLogger("urllib3").setLevel(logging.ERROR)

        try:
            self.t = Tracing(t_host, t_port, '', False)
            monitoring_url = "http://{}:{}".format(m_host, m_port)
            self.m = Monitoring(monitoring_url)
            self.c = CassandraOps(c_hosts, int(c_port))
            self.c.set_prepared()
            self.r = RedisOps()
        except Exception as e:
                logging.debug(e)

    # Toplevel tracing retrieval and batch insert
    def get_tracing(self, time_back=300):
        try:
            services = self.r.get_services()
            for service in services:
                traces = self.t.getTraces(service.replace("_", "-"), time_back,
                                          '20000')
                try:
                    self.set_tracing(traces)
                except Exception as e:
                    logging.debug(e)

            # Update list of available services from tracing
            services = self.t.getServices()
            self.r.set_tracing_services(services)
        except Exception as e:
            logging.debug(e)

    # Insert to cassandra visibility traces and spans tables
    def set_tracing(self, trace):
        for traces in trace['data']:
            self.c.set_batch()
            for spans in traces['spans']:
                try:
                    span = {}
                    span['spanID'] = spans['spanID']
                    span['duration'] = spans['duration']
                    span['startTime'] = spans['startTime']
                    span['operationName'] = spans['operationName']

                    tag = {}
                    for tags in spans['tags']:
                        tag[tags['key']] = tags['value']
                    self.c.insert_span(traces['traceID'], span, tag)
                except Exception as e:
                    logging.debug("spans loop")
                    logging.debug(e)

            process_list = []
            for p in traces['processes']:
                process_list.append(p)
            service_names = []
            for pname in process_list:
                service_names.append(traces['processes'][pname]['serviceName'])
            try:
                self.c.insert_trace(traces['traceID'], service_names)
                self.c.execute_batch()
            except Exception as e:
                logging.debug(e)

    # Insert to cassandra visibility metrics table
    def get_monitoring(self):

        try:
            # Fetch collector service/metric lists from redis
            service_names = self.r.get_services()
            metric_prefixes, metric_suffixes = self.r.get_metrics()

            self.c.set_batch()
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
                            mn = data[
                                    'data']['result'][0]['metric']['__name__']
                            self.c.insert_metric(
                                           mn, m_value, str(m_time), sname)

                            # Add to redis temporarily
                            self.r.r.set(mn, m_value)

                        except Exception as e:
                            logging.debug(e)
            self.c.execute_batch()
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
    if isinstance(args['c_hosts'], basestring):
        ch = ast.literal_eval(args['c_hosts'])
    else:
        ch = args['c_hosts']

    c = Collector(args['t_port'], args['t_host'], args['m_port'],
                  args['m_host'], args['c_port'], ch)

    # Collector loop
    loop = True
    while loop:
        try:
            c.get_tracing()
            c.get_monitoring()
            time.sleep(int(args['sinterval']))
        except KeyboardInterrupt:
            loop = False
        except Exception as e:
            logging.debug(e)


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

    args, unknown = parser.parse_known_args()
    print(main(vars(args)))
