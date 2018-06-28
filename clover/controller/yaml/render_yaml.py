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
            snort_grpc_port=args['snort_grpc_port'],
            nginx_grpc_port=args['nginx_grpc_port'],
            redis_port=args['redis_port'],
            cass_port=args['cass_port'],
            node_port=args['node_port']
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
            '--image_name', default='clover-controller',
            help='The image name to use')
    parser.add_argument(
            #'--image_path', default='opnfv',
            '--image_path', default='localhost:5000',
            help='The path to the image to use')
    parser.add_argument(
            #'--image_tag', default='opnfv-6.0.0',
            '--image_tag', default='latest',
            help='The image tag to use')
    parser.add_argument(
            '--deploy_name', default='clover-controller',
            help='The k8s deploy name to use')
    parser.add_argument(
            '--redis_port', default='6379',
            help='The redis port to connect for management')
    parser.add_argument(
            '--snort_grpc_port', default='50052',
            help='The GRPC port for snort service')
    parser.add_argument(
            '--nginx_grpc_port', default='50054',
            help='The GRPC port for nginx services')
    parser.add_argument(
            '--node_port', default='32044',
            help='Default nodePort port number')
    parser.add_argument(
            '--cass_port', default='9042',
            help='The Cassandra port')

    args = parser.parse_args()
    print(render_yaml(vars(args)))
