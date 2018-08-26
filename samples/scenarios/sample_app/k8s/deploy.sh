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
CLOVER_WORK_DIR=${CLOVER_BASE_DIR}/work
SAMPLE_APP_DIR=${CLOVER_BASE_DIR}/samples/scenarios/sample_app/k8s/

REPLICAS_CANARY=3
REPLICAS_PROD=3
NAMESPACE_CANARY=ci-cd-demo
NAMESPACE_PROD=ci-cd-demo
# Fetch newest image version
IMAGE_VER=$(wget -q \
	    https://registry.hub.docker.com//v1/repositories/opnfv/clover/tags \
	    -O - \
	    # NOTE: remaining part after the pipe can be easily replaced with jq
            # if jq is installed
	    | sed -e 's/[][]//g' -e 's/"//g' -e 's/ //g' | tr '}' '\n'  | \
	    awk -F: '{print $3}' | grep opnfv | tail -n1)


pushd ${SAMPLE_APP_DIR}

# Update yaml files
for file in deployments/* services/* namespaces/*
do
  sed -i "s/__NAMESPACE_CANARY__/${NAMESPACE_CANARY}/g" ${file}
  if grep --quiet "kind: Deployment" ${file}; then
    sed -i "s/__REPLICAS_CANARY__/${REPLICAS_CANARY}/g" ${file}
    sed -i "s/__IMAGE_VER__/${IMAGE_VER}/g" ${file}
  fi
done

# Create namespaces
kubectl apply -f ./namespaces

# Deploy services
kubectl apply -f ./services

# Deploy the latest image to canary
kubectl apply -f ./deployments/canary.yaml

# Manual intervention needed to deploy to production
# NOTE: waiting for 5 seconds as a mock for manual
# permission to deploy the app to production stack
sleep 5

# Deploy to production stack
kubectl apply -f ./deployments/prod.yaml

popd


