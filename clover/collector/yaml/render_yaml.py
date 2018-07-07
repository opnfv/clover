# Copyright (c) Authors of Clover
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0

import argparse

from jinja2 import Template


def render_yaml(args):
    template_file = 'manifest.template'
    out_file = args['deploy_name'] + '.yaml'

    try:
        with open(template_file) as f:
            tmpl = Template(f.read())
        output = tmpl.render(
            image_path=args['image_path'],
            image_name=args['image_name'],
            image_tag=args['image_tag'],
            deploy_name=args['deploy_name'],
            grpc_port=args['grpc_port'],
            monitor_port=args['monitor_port'],
            redis_port=args['redis_port'],
            cass_port=args['cass_port'],
            trace_port=args['trace_port']
        )
        with open(out_file, "wb") as fh:
            fh.write(output)
        return "Generated manifest for {}".format(args['deploy_name'])
    except Exception as e:
        print(e)
        return "Unable to generate manifest for {}".format(
                                        args['deploy_name'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
            '--image_name', default='clover-collector',
            help='The image name to use')
    parser.add_argument(
            # '--image_path', default='opnfv',
            '--image_path', default='localhost:5000',
            help='The path to the image to use')
    parser.add_argument(
            # '--image_tag', default='opnfv-6.0.0',
            '--image_tag', default='latest',
            help='The image tag to use')
    parser.add_argument(
            '--deploy_name', default='clover-collector',
            help='The k8s deploy name to use')
    parser.add_argument(
            '--redis_port', default='6379',
            help='The redis port to connect for management')
    parser.add_argument(
            '--monitor_port', default='9090',
            help='The Prometheus monitoring port')
    parser.add_argument(
            '--grpc_port', default='50054',
            help='The GRPC server port for collector management')
    parser.add_argument(
            '--trace_port', default='16686',
            help='The Jaeger tracing port')
    parser.add_argument(
            '--cass_port', default='9042',
            help='The Cassandra port')

    args = parser.parse_args()
    print(render_yaml(vars(args)))
