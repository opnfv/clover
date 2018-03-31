#!/bin/bash
#
# Copyright (c) Authors of Clover
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
#

CLOVER_BASE_DIR=$(cd ${BASH_SOURCE[0]%/*}/..;pwd)
IMAGE_PATH=${IMAGE_PATH:-"localhost:5000"}
IMAGE_NAME=${IMAGE_NAME:-"clover"}

cd $CLOVER_BASE_DIR
docker build -f docker/Dockerfile -t $IMAGE_NAME .
docker tag $IMAGE_NAME $IMAGE_PATH/$IMAGE_NAME
docker push $IMAGE_PATH/$IMAGE_NAME
