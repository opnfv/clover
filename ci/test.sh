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
CLOVER_IMAGE="opnfv/clover:latest"

sudo docker pull $CLOVER_IMAGE

# Setup clover kubernetes env
sudo docker run --rm \
    -v ~/.kube/config:/root/.kube/config \
    -v $CLOVER_BASE_DIR:/home/opnfv/repos/clover \
    $CLOVER_IMAGE \
    /bin/bash -c '/home/opnfv/repos/clover/docker/setup_clover_k8s_env.sh'

# Run clover kubernetes env validation
sudo docker run --rm \
    -v ~/.kube/config:/root/.kube/config \
    -v $CLOVER_BASE_DIR:/home/opnfv/repos/clover \
    $CLOVER_IMAGE \
    /bin/bash -c '/home/opnfv/repos/clover/docker/validate_clover_k8s_env.sh'

echo "Clover test complete!"
