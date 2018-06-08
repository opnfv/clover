#!/bin/bash

set -e
set -x

CLOVER_DIR=`cd ${BASH_SOURCE[0]%/*}/;pwd`
export CLOVER_DIR

# Set the variable for deploying k8s
export XCI_FLAVOR=${XCI_FLAVOR:-mini}
export INSTALLER_TYPE=${INSTALLER_TYPE:-kubespray}
export DEPLOY_SCENARIO=${DEPLOY_SCENARIO:-k8-flannel-nofeature}

if [[ $(whoami) == "root" ]]; then
    echo "ERROR: This script should not be run as root!"
    exit 1
fi

WORK_DIR=${CLOVER_DIR}/work
sudo rm -rf $WORK_DIR
mkdir $WORK_DIR

# If SSH key doesn't exist generate an SSH key in $HOME/.ssh/
[[ ! -d "$HOME/.ssh/" ]] && mkdir $HOME/.ssh/
[[ ! -f "$HOME/.ssh/id_rsa" ]] && ssh-keygen -q -t rsa -f ~/.ssh/id_rsa -N ""

sudo apt-get update
sudo apt-get install git python-pip -y

git clone https://gerrit.opnfv.org/gerrit/releng-xci $WORK_DIR/releng-xci

cd $WORK_DIR/releng-xci/xci

source xci-deploy.sh

MASTER_IP=$(ssh root@$OPNFV_HOST_IP  "grep -r server ~/.kube/config | awk '{print \$2}' |awk -F '[:/]' '{print \$4}'")
echo "----------------------------------------"
echo "Info: You can login the Kubernetes Cluster master host"
echo "ssh root@$MASTER_IP"
echo "----------------------------------------"
