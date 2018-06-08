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

# test line ##### ####

CLOVER_BASE_DIR=$(cd ${BASH_SOURCE[0]%/*}/..;pwd)
CLOVER_WORK_DIR=$CLOVER_BASE_DIR/work
CLOVER_WORK_DIR_CONTAINER4NFV=$CLOVER_WORK_DIR/container4nfv
MASTER_NODE_NAME="master"
SSH_OPTIONS="-o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no"
K8S_ISTIO_DEPLOY_TIMEOUT=3600

FUNCTEST_IMAGE="opnfv/functest-kubernetes:latest"
INSTALLER_TYPE="container4nfv"
DEPLOY_SCENARIO="k8-istio-clover"

mkdir -p $CLOVER_WORK_DIR
# Fetch container4nfv source code
if [ -d $CLOVER_WORK_DIR_CONTAINER4NFV ]; then
    rm -rf $CLOVER_WORK_DIR_CONTAINER4NFV
fi
git clone https://git.opnfv.org/container4nfv/ $CLOVER_WORK_DIR_CONTAINER4NFV
pushd $CLOVER_WORK_DIR_CONTAINER4NFV

# Create kubernetes + istio env
timeout $K8S_ISTIO_DEPLOY_TIMEOUT ./src/vagrant/kubeadm_istio/deploy.sh

popd

# Fetch kube-master node info
pushd $CLOVER_WORK_DIR_CONTAINER4NFV/src/vagrant/kubeadm_istio
MASTER_NODE_HOST=$(vagrant ssh-config $MASTER_NODE_NAME | awk '/HostName /{print $2}')
MASTER_NODE_USER=$(vagrant ssh-config $MASTER_NODE_NAME | awk '/User /{print $2}')
MASTER_NODE_KEY=$(vagrant ssh-config $MASTER_NODE_NAME | awk '/IdentityFile /{print $2}')

# Push clover source code to kube-master node
ssh $SSH_OPTIONS -i $MASTER_NODE_KEY ${MASTER_NODE_USER}@${MASTER_NODE_HOST} rm -rf clover
scp $SSH_OPTIONS -i $MASTER_NODE_KEY -r $CLOVER_BASE_DIR ${MASTER_NODE_USER}@${MASTER_NODE_HOST}:clover

# Run test
ssh $SSH_OPTIONS -i $MASTER_NODE_KEY ${MASTER_NODE_USER}@${MASTER_NODE_HOST} ./clover/ci/test.sh

popd

echo "Clover deploy complete!"

###############################################################################
# Prepare and run functest.
# TODO: Use jenkins to trigger functest job.

# Setup configuration file for running functest
mkdir -p $CLOVER_WORK_DIR/functest/results
scp $SSH_OPTIONS -i $MASTER_NODE_KEY \
    ${MASTER_NODE_USER}@${MASTER_NODE_HOST}:.kube/config \
    $CLOVER_WORK_DIR/functest/kube-config
RC_FILE=$CLOVER_WORK_DIR/functest/k8.creds
echo "export KUBERNETES_PROVIDER=local" > $RC_FILE
KUBE_MASTER_URL=$(cat $CLOVER_WORK_DIR/functest/kube-config | grep server | awk '{print $2}')
echo "export KUBE_MASTER_URL=$KUBE_MASTER_URL" >> $RC_FILE
KUBE_MASTER_IP=$(echo $KUBE_MASTER_URL | awk -F'https://|:[0-9]+' '$0=$2')
echo "export KUBE_MASTER_IP=$KUBE_MASTER_IP" >> $RC_FILE

# Run functest
sudo docker pull $FUNCTEST_IMAGE
sudo docker run --rm \
    -e INSTALLER_TYPE=$INSTALLER_TYPE \
    -e NODE_NAME=$NODE_NAME \
    -e DEPLOY_SCENARIO=$DEPLOY_SCENARIO \
    -e BUILD_TAG=$BUILD_TAG \
    -v $RC_FILE:/home/opnfv/functest/conf/env_file \
    -v $CLOVER_WORK_DIR/functest/results:/home/opnfv/functest/results \
    -v $CLOVER_WORK_DIR/functest/kube-config:/root/.kube/config \
    $FUNCTEST_IMAGE \
    /bin/bash -c 'run_tests -r -t all'

echo "Clover run functest complete!"
###############################################################################
