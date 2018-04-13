#!/bin/bash
#
# Copyright (c) Authors of Clover
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
#

CLOVER_BASE_DIR=${CLOVER_BASE_DIR:-"/home/opnfv/repos/clover"}
ISTIO_BASE_DIR=${ISTIO_BASE_DIR:-"/istio-source"}

cd $CLOVER_BASE_DIR

echo "Deploying Prometheus monitoring"

kubectl apply -f $ISTIO_BASE_DIR/install/kubernetes/addons/prometheus.yaml

echo "Deploying Jaeger tracing"

kubectl apply -n istio-system -f https://raw.githubusercontent.com/jaegertracing/jaeger-kubernetes/master/all-in-one/jaeger-all-in-one-template.yml

echo "Exposing tracing and monitoring outside of Kubernetes cluster"

kubectl delete -n istio-system svc prometheus

kubectl expose -n istio-system deployment jaeger-deployment --port=16686 --type=NodePort

kubectl expose -n istio-system deployment prometheus --port=9090 --type=NodePort
