#!/bin/bash
#
# Copyright (c) Authors of Clover
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
#
set -ex

CLOVER_BASE_DIR=$(cd ${BASH_SOURCE[0]%/*}/..;pwd)

cd $CLOVER_BASE_DIR
pip install --upgrade ./

kubectl apply -f ./clover/logging/install

kubectl apply -f /usr/local/istio-source/install/kubernetes/addons/prometheus.yaml

kubectl apply -f ./clover/tools/yaml/redis.yaml

kubectl apply -n istio-system -f https://raw.githubusercontent.com/jaegertracing/jaeger-kubernetes/master/all-in-one/jaeger-all-in-one-template.yml

# TODO: Add waiting for all pods running

echo "Setup Clover Kubernetes environment complete!"
