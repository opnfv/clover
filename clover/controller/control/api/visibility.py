# Copyright (c) Authors of Clover
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0

from flask import Blueprint, request, jsonify, Response
import redis
import logging
import collector

visibility_api = Blueprint('visibility_api', __name__)

HOST_IP = 'redis.default'


@visibility_api.route("/visibility/clear")
def clear_visibility():
    # Zero out or delete redis keys with results
    r = redis.StrictRedis(host=HOST_IP, port=6379, db=0)
    r.set('proxy_rt', 0)
    r.set('trace_count', 0)
    r.set('span_count', 0)
    del_keys = ['span_user_agent', 'span_urls', 'span_urls_z',
                'span_status_codes_z', 'span_node_url_z', 'span_node_id_z',
                'span_user_agent_z']
    for dk in del_keys:
        r.delete(dk)
    # Truncate cassandra tables
    return collector.truncate()


@visibility_api.route(
             "/visibility/get/stats/<s_type>", methods=['GET', 'POST'])
def get_visibility_stats(s_type):
    try:

        p = request.json
        if not p:
            stat_type = s_type
        else:
            stat_type = p['stat_type']

        r = redis.StrictRedis(host=HOST_IP, port=6379, db=0)

        content = {}
        if stat_type == 'system' or s_type == 'all':
            content['trace_count'] = r.get('trace_count')
            content['span_count'] = r.get('span_count')
        if stat_type == 'metrics' or s_type == 'all':
            content['metrics_test'] = r.lrange('metrics_test', 0, 200)
        if stat_type == 'tracing' or s_type == 'all':
            content['proxy_rt'] = r.get('proxy_rt')
            content['span_urls'] = list(r.smembers('span_urls'))
            content['user_agents'] = list(r.smembers('span_user_agent'))
            content['user_agent_count'] = r.zrange(
                                       "span_user_agent_z", 0, 50, False, True)
            content['request_url_count'] = r.zrange(
                                             "span_urls_z", 0, 50, False, True)
            content['status_code_count'] = r.zrange(
                                     "span_status_codes_z", 0, 50, False, True)
            content['node_url_count'] = r.zrange(
                                         "span_node_url_z", 0, 50, False, True)
            content['node_id_count'] = r.zrange(
                                          "span_node_id_z", 0, 50, False, True)

        response = jsonify(content)
        return response
    except Exception as e:
        logging.debug(e)
        return Response("Error getting visibility stats", status=400)


@visibility_api.route("/visibility/get/<c_type>", methods=['GET', 'POST'])
def get_visibility_config(c_type):
    try:

        r = redis.StrictRedis(host=HOST_IP, port=6379, db=0)

        content = {}

        if c_type == 'services' or c_type == 'all':
            services = list(r.smembers('visibility_services'))
            content['visibility_services'] = services
        if c_type == 'metrics' or c_type == 'all':
            content['metric_prefixes'] = list(r.smembers('metric_prefixes'))
            content['metric_suffixes'] = list(r.smembers('metric_suffixes'))
            content['custom_metrics'] = list(r.smembers('custom_metrics'))

        response = jsonify(content)
        return response
    except Exception as e:
        logging.debug(e)
        return Response("Error getting visibility config", status=400)


@visibility_api.route("/visibility/set", methods=['GET', 'POST'])
def set_visibility():
    return collector.set_collector()
