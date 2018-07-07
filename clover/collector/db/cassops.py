# Copyright (c) Authors of Clover
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0

from cassandra.cluster import Cluster
from cassandra.query import BatchStatement
import logging

CASSANDRA_HOSTS = ['cassandra.default']


class CassandraOps:

    def __init__(self, hosts, port=9042, keyspace='visibility'):
        logging.basicConfig(filename='cassops.log',
                            level=logging.DEBUG)
        cluster = Cluster(hosts, port=port)
        self.session = cluster.connect()
        self.keyspace = keyspace

    def truncate(self, tables=['traces', 'metrics', 'spans']):
        self.session.set_keyspace(self.keyspace)
        try:
            for table in tables:
                self.session.execute("""
                        TRUNCATE %s
                        """ % table)
        except Exception as e:
            logging.debug(e)

    def init_visibility(self):
        try:
            self.session.execute("""
                    CREATE KEYSPACE %s
                    WITH replication = { 'class': 'SimpleStrategy',
                    'replication_factor': '1' }
                    """ % self.keyspace)
        except Exception as e:
            logging.debug(e)

        self.session.set_keyspace(self.keyspace)

        try:
            self.session.execute("""
                    CREATE TABLE IF NOT EXISTS traces (
                        traceid text,
                        processes list<text>,
                        PRIMARY KEY (traceid)
                    )
                    """)

            self.session.execute("""
                    CREATE TABLE IF NOT EXISTS spans (
                        spanid text,
                        traceid text,
                        duration int,
                        start_time int,
                        processid text,
                        operation_name text,
                        node_id text,
                        http_url text,
                        upstream_cluster text,
                        PRIMARY KEY (spanid, traceid)
                    )
                    """)

            self.session.execute("""
                    CREATE TABLE IF NOT EXISTS metrics (
                        m_name text,
                        m_value text,
                        m_time text,
                        service text,
                        monitor_time timestamp,
                        PRIMARY KEY (m_name, monitor_time)
                    )
                    """)
        except Exception as e:
            logging.debug(e)

    def set_prepared(self):
        self.session.set_keyspace(self.keyspace)
        self.insert_tracing_stmt = self.session.prepare(
            """
            INSERT INTO spans (spanid, traceid, duration, operation_name,
            node_id, http_url, upstream_cluster)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """
        )
        self.insert_metric_stmt = self.session.prepare(
            """
            INSERT INTO metrics
            (m_name, m_value, m_time, service, monitor_time)
            VALUES (?, ?, ?, ?, toTimestamp(now()))
            """
        )

    def set_batch(self):
        self.batch = BatchStatement()

    def execute_batch(self):
        self.session.execute(self.batch)

    def insert_tracing(self, table, traceid, s, tags):
        self.session.set_keyspace(self.keyspace)
        if 'upstream_cluster' not in tags:
            logging.debug('NO UPSTREAM_CLUSTER KEY')
            tags['upstream_cluster'] = 'none'
        try:
            self.batch.add(self.insert_tracing_stmt,
                           (s['spanID'], traceid, s['duration'],
                            s['operationName'], tags['node_id'],
                            tags['http.url'], tags['upstream_cluster']))
        except Exception as e:
            logging.debug('{} {} {} {} {} {} {}'.format(s['spanID'], traceid,
                          s['duration'], s['operationName'], tags['node_id'],
                          tags['http.url'], tags['upstream_cluster']))
            logging.debug(e)

    def insert_trace(self, traceid, processes):
        self.session.set_keyspace(self.keyspace)
        self.session.execute(
            """
            INSERT INTO traces (traceid, processes)
            VALUES (%s, %s)
            """,
            (traceid,  processes)
        )

    def insert_metric(self, m_name, m_value, m_time, service):
        self.session.set_keyspace(self.keyspace)
        self.batch.add(self.insert_metric_stmt,
                       (m_name, m_value, m_time, service))


def main():
    cass = CassandraOps(CASSANDRA_HOSTS)
    cass.init_visibility()


if __name__ == '__main__':
    main()
