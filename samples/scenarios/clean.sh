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

echo "Deleting Service Delivery Controller sample scenario"

kubectl delete -f ./samples/scenarios/service_delivery_controller_opnfv.yaml

echo "Deleting Istio"

kubectl delete -f $ISTIO_BASE_DIR/install/kubernetes/istio.yaml

echo "Deleting Prometheus monitoring and Jaeger Tracing"

kubectl delete -n istio-system -f https://raw.githubusercontent.com/jaegertracing/jaeger-kubernetes/master/all-in-one/jaeger-all-in-one-template.yml

kubectl delete -f $ISTIO_BASE_DIR/install/kubernetes/addons/prometheus.yaml
