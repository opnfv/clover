# Copyright (c) Authors of Clover
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0

INDEX_PATTERN='logstash-*'
TAG='newlog.logentry.istio-system'

def test_health(es):
    assert es.cat.health(h='status') != 'red\n'

def test_indices(es):
    assert len(es.cat.indices(INDEX_PATTERN)) > 0

def test_logentry(es):
    assert es.count(
        index=INDEX_PATTERN,
        body={"query":{"match":{"tag":TAG}}})['count'] > 0

def test_lb(es):
    """requests in and out load balance should match"""
    from_lb = es.count(
        index=INDEX_PATTERN,
        body={"query":{"match":{"source": "http-lb"}}})
    to_lb = es.count(
        index=INDEX_PATTERN,
        body={"query":{"match":{"destination": "http-lb"}}})
    assert from_lb['count'] == to_lb['count']
