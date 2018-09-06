#!/bin/bash

# Copyright (c) Authors of Clover
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0

set -ex

NAMESPACE='clover-cd'
SOURCE_DIR=$(cd $(dirname ${BASH_SOURCE[0]})/;pwd)

update_templates()
{
  pushd "${SOURCE_DIR}"/resources
  for template in *.yaml
  do
    sed -i "s/__NAMESPACE__/${NAMESPACE}/g" "${template}"
  done
  popd
}

deploy()
{
  pushd ${SOURCE_DIR}/resources
  kubectl apply -f namespace.yaml
  kubectl apply -f pvc.yaml
  kubectl apply -f configmap.yaml
  kubectl apply -f secrets.yaml
  kubectl apply -f svc.yaml
  kubectl apply -f svc-agent.yaml
  kubectl apply -f deployment.yaml
  popd
}

update_templates
deploy
