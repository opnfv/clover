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
    out_file = 'snort.yaml'

    try:
        with open(template_file) as f:
            tmpl = Template(f.read())
        output = tmpl.render(
            image_path=args['image_path'],
            image_name=args['image_name'],
            image_tag=args['image_tag'],
            deploy_name=args['deploy_name'],
            grpc_port=args['grpc_port'],
            pac_port=args['pac_port'],
            redis_port=args['redis_port'],
            http_port=args['http_port']
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
            '--image_name', default='clover-ns-snort-ids',
            help='The image name to use')
    parser.add_argument(
            '--image_path', default='opnfv',
            help='The path to the image to use')
    parser.add_argument(
            '--image_tag', default='opnfv-6.0.0',
            help='The image tag to use')
    parser.add_argument(
            '--deploy_name', default='snort-ids',
            help='The k8s deploy name to use')
    parser.add_argument(
            '--redis_port', default='6379',
            help='The redis port to connect to for alerts')
    parser.add_argument(
            '--http_port', default='80',
            help='Analyze http data-plane traffic on this port')
    parser.add_argument(
            '--grpc_port', default='50052',
            help='The GRPC server port for snort management')
    parser.add_argument(
            '--pac_port', default='50054',
            help='The GRPC server port of the service to send alerts on')

    args = parser.parse_args()
    print(render_yaml(vars(args)))
