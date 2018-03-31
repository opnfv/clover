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
    server_port = '9180'
    grpc_port = '50054'
    if args['service_type'] == 'lb':
        out_file = 'lb.yaml'
        deploy_name = 'http-lb'
    elif args['service_type'] == 'proxy':
        out_file = 'proxy.yaml'
        deploy_name = 'proxy-access-control'
    elif args['service_type'] == 'server':
        out_file = 'server.yaml'
        deploy_name = 'clover-server'
    else:
        return "Invalid service type: {}".format(args['service_type'])

    try:
        with open(template_file) as f:
            tmpl = Template(f.read())
        output = tmpl.render(
            image_path=args['image_path'],
            image_name=args['image_name'],
            image_tag=args['image_tag'],
            deploy_name=deploy_name,
            server_port=server_port,
            grpc_port=grpc_port
        )
        with open(out_file, "wb") as fh:
            fh.write(output)
        return "Generated manifest for {}".format(args['service_type'])
    except Exception as e:
        print(e)
        return "Unable to generate manifest for {}".format(
                                        args['service_type'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
            '--service_type', required=True,
            help='The service to generate k8s manifest for')
    parser.add_argument(
            '--image_name', required=True,
            help='The image name to use')
    parser.add_argument(
            '--image_path', default='localhost:5000',
            help='The path to the images to use')
    parser.add_argument(
            '--image_tag', default='latest',
            help='The image tag to use')
    args = parser.parse_args()
    print(render_yaml(vars(args)))
