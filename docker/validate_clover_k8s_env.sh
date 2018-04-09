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
PATH="$PATH:/usr/local/istio-source/bin"

SDC_NAMESPACE="default"
SDC_SCENARIO_PODS_PREFIX="clover-server1,clover-server2,clover-server3,clover-server4,clover-server5,http-lb-v1,http-lb-v2,proxy-access-control,redis,snort-ids"


cd $CLOVER_BASE_DIR
pip install --upgrade ./

# Validate logging
python clover/logging/validate.py

# Validate monitoring
kubectl -n istio-system port-forward $(kubectl -n istio-system get pod -l app=prometheus -o jsonpath='{.items[0].metadata.name}') 9090:9090 &
sleep 1
python clover/monitoring/validate.py

# Validate tracing
kubectl -n istio-system port-forward $(kubectl -n istio-system get pod -l app=jaeger -o jsonpath='{.items[0].metadata.name}') 16686:16686 &
sleep 1
python clover/tracing/validate.py

# Deploy SDC scenario
kubectl apply -f <(istioctl kube-inject -f samples/scenarios/service_delivery_controller_opnfv.yaml)
clover/tools/wait_for_pods.py $SDC_NAMESPACE $SDC_SCENARIO_PODS_PREFIX  running
kubectl port-forward $(kubectl get pod -l name=redis -o jsonpath='{.items[0].metadata.name}') 6379:6379 &
sleep 1

# TODO: Validate rr

echo "Verify Clover Kubernetes environment complete!"
