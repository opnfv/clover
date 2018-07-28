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
            ssl_port=args['ssl_port'],
            rmi_port=args['rmi_port'],
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
            '--image_name', default='clover-jmeter-master',
            help='The image name to use')
    parser.add_argument(
            '--image_path', default='localhost:5000',
            help='The path to the image to use')
    parser.add_argument(
            '--image_tag', default='latest',
            help='The image tag to use')
    parser.add_argument(
            '--deploy_name', default='clover-jmeter-master',
            help='The k8s deploy name to use')
    parser.add_argument(
            '--rmi_port', default='1099',
            help='The master-slave remote method invocation port')
    parser.add_argument(
            '--http_port', default='80',
            help='HTTP data-plane traffic')
    parser.add_argument(
            '--grpc_port', default='50054',
            help='The GRPC server port for management')
    parser.add_argument(
            '--ssl_port', default='443',
            help='HTTPS data-plane traffic')

    args = parser.parse_args()
    print(render_yaml(vars(args)))
