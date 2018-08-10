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

echo "Deploying Istio manual sidecar injection without TLS authentication"

kubectl apply -f $ISTIO_BASE_DIR/install/kubernetes/istio-demo.yaml

echo "Deploying Service Delivery Controller sample scenario"

kubectl apply -f <(istioctl kube-inject --debug -f ./samples/scenarios/service_delivery_controller_opnfv.yaml)
