# Copyright (c) Authors of Clover
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0

from flask import Blueprint, render_template, abort
from jinja2 import TemplateNotFound
import redis
import logging

visibility = Blueprint('visibility', __name__)


HOST_IP = 'redis.default'


@visibility.route('/')
@visibility.route('/visibility')
def show():
    try:
        r = redis.StrictRedis(host=HOST_IP, port=6379, db=0)

        vservices = list(r.smembers('visibility_services'))
        tracing_services = list(r.smembers('tracing_services'))
        op_names = list(r.smembers('span_operation_name'))
        request_urls = list(r.smembers('span_urls'))
        user_agents = list(r.smembers('span_user_agent'))
        node_ids = list(r.smembers('span_node_id'))
        upstream_cluster = list(r.smembers('span_upstream_cluster'))
        status_codes = list(r.smembers('span_status_code'))

        # Get per service aggregate stats
        metric_prefixes = r.smembers('metric_prefixes')
        metric_suffixes = r.smembers('metric_suffixes')
        metric_list = {}
        for sname in vservices:
            for prefix in metric_prefixes:
                for suffix in metric_suffixes:
                    try:
                        metric_name = prefix + sname + suffix
                        metric_count = r.get(metric_name)
                        metric_list[metric_name] = metric_count
                    except Exception as e:
                        logging.debug(e)

        return render_template('visibility.html', vservices=vservices,
                               tracing_services=tracing_services,
                               op_names=op_names,
                               request_urls=request_urls,
                               status_codes=status_codes,
                               user_agents=user_agents,
                               node_ids=node_ids,
                               upstream_cluster=upstream_cluster,
                               metric_list=metric_list,
                               view_title="Visibility Dashboard")
    except TemplateNotFound:
        abort(404)
    except Exception as e:
        logging.debug(e)


@visibility.route('/visibility/metrics')
def get_metrics():
    try:
        r = redis.StrictRedis(host=HOST_IP, port=6379, db=0)
        # Get per service aggregate stats
        vservices = list(r.smembers('visibility_services'))
        metric_prefixes = r.smembers('metric_prefixes')
        metric_suffixes = r.smembers('metric_suffixes')
        metric_list = {}
        for sname in vservices:
            for prefix in metric_prefixes:
                for suffix in metric_suffixes:
                    try:
                        metric_name = prefix + sname + suffix
                        metric_count = r.get(metric_name)
                        metric_list[metric_name] = metric_count
                    except Exception as e:
                        logging.debug(e)
        return render_template('metric_requests.html', metric_list=metric_list)
    except TemplateNotFound:
        abort(404)
    except Exception as e:
        logging.debug(e)
