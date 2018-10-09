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

# Deploy Clover SDC sample
kubectl apply -f <(istioctl kube-inject -f ~/clover/samples/scenarios/service_delivery_controller_opnfv.yaml)

# Wait for SDC sample deployed
kubectl get services
kubectl get pods

r="0"
while [ $r -ne "10" ]
do
   sleep 30
   kubectl get pods
   r=$(kubectl get pods | grep Running | wc -l)
done

echo "Set up Clover SDC sample complete!"
