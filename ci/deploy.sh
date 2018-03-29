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

CLOVER_BASE_DIR=`cd ${BASH_SOURCE[0]%/*}/..;pwd`
CLOVER_WORK_DIR=$CLOVER_BASE_DIR/work
MASTER_NODE_NAME='master'
SSH_OPTIONS="-o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no"
K8S_ISTIO_DEPLOY_TIMEOUT=3600

mkdir -p $CLOVER_WORK_DIR
cd $CLOVER_WORK_DIR

# Fetch container4nfv source code
if [ -d container4nfv ]; then
    rm -rf container4nfv
fi
git clone https://git.opnfv.org/container4nfv/
cd container4nfv

# Create kubernetes + istio env
timeout $K8S_ISTIO_DEPLOY_TIMEOUT ./src/vagrant/kubeadm_istio/deploy.sh

# Fetch kube-master node info
cd src/vagrant/kubeadm_istio
MASTER_NODE_HOST=$(vagrant ssh-config $MASTER_NODE_NAME | awk '/HostName /{print $2}')
MASTER_NODE_USER=$(vagrant ssh-config $MASTER_NODE_NAME | awk '/User /{print $2}')
MASTER_NODE_KEY=$(vagrant ssh-config $MASTER_NODE_NAME | awk '/IdentityFile /{print $2}')

# Push clover source code to kube-master node
ssh $SSH_OPTIONS -i $MASTER_NODE_KEY ${MASTER_NODE_USER}@${MASTER_NODE_HOST} rm -rf clover
scp $SSH_OPTIONS -i $MASTER_NODE_KEY -r $CLOVER_BASE_DIR ${MASTER_NODE_USER}@${MASTER_NODE_HOST}:clover

# Run test
ssh $SSH_OPTIONS -i $MASTER_NODE_KEY ${MASTER_NODE_USER}@${MASTER_NODE_HOST} ./clover/ci/test.sh

echo "Clover deploy complete!"
