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

ISTIO_NAMESPACE="istio-system"
LOGGING_NAMESPACE="logging"
MONITORING_NAMESPACE=$ISTIO_NAMESPACE
TRACING_NAMESPACE=$ISTIO_NAMESPACE

LOGGING_PODS_PREFIX="elasticsearch,fluentd-es,kibana"
MONITORING_PODS_PREFIX="prometheus"
TRACING_PODS_PREFIX="jaeger-deployment"

cd $CLOVER_BASE_DIR
pip install --upgrade ./

kubectl apply -f ./clover/logging/install
clover/tools/wait_for_pods.py $LOGGING_NAMESPACE $LOGGING_PODS_PREFIX running

kubectl apply -f /usr/local/istio-source/install/kubernetes/addons/prometheus.yaml
clover/tools/wait_for_pods.py $MONITORING_NAMESPACE $MONITORING_PODS_PREFIX running

kubectl apply -n istio-system -f https://raw.githubusercontent.com/jaegertracing/jaeger-kubernetes/master/all-in-one/jaeger-all-in-one-template.yml
clover/tools/wait_for_pods.py $TRACING_NAMESPACE $TRACING_PODS_PREFIX running

echo "Setup Clover Kubernetes environment complete!"
