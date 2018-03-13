# Copyright (c) Authors of Clover
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0

from kubernetes import client, config
from kubernetes.stream import stream
import sh
import re

FLUENTD_NAMESPACE = 'logging'
FLUENTD_PATTERN = 'fluentd-.*'
FLUENTD_LABELS = 'app=fluentd-es'
FLUENTD_INPUT = """<source>
  type forward
</source>"""

def main():
    # Load config from default location.
    config.load_kube_config()

    v1 = client.CoreV1Api()

    fluentd_pod_name = None

    # find by name
    print("Find fluentd pod by name '{}'".format(FLUENTD_PATTERN))
    fluentd_regex = re.compile(FLUENTD_PATTERN)
    resp = v1.list_namespaced_pod(FLUENTD_NAMESPACE)
    for i in resp.items:
        if fluentd_regex.search(i.metadata.name) is not None:
            print(i.metadata.name)

    # find by label selector
    print("Find fluentd pod by label selector '{}'".format(FLUENTD_LABELS))
    resp = v1.list_namespaced_pod(FLUENTD_NAMESPACE, label_selector=FLUENTD_LABELS)
    for i in resp.items:
        print(i.metadata.name)
        fluentd_pod_name = i.metadata.name

    # check fluentd configuration
    # NOTE: exec in Python librarry does not work well, use shell command as a workaround
    # See https://github.com/kubernetes-client/python/issues/485
    result = sh.kubectl('exec -n logging fluentd-es-7b48cb5f9c-n7cgq cat /etc/fluent/config.d/forward.input.conf'.split())
    if FLUENTD_INPUT in result:
        print("fluentd input configured correctly")
    else:
        print("fluentd input not configured\n{}".format(FLUENTD_INPUT))

if __name__ == '__main__':
    main()
