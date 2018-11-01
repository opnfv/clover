#!/bin/bash
#
# Copyright (c) Authors of Clover
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0

IMAGE_PATH=${IMAGE_PATH:-"kube1-node1:5000"}
IMAGE_NAME=${IMAGE_NAME:-"clover-spark:latest"}

# Copy clover-spark jar first
cp ../../target/scala-2.11/clover-spark_2.11-1.0.jar jars/

docker build -t $IMAGE_NAME -f Dockerfile .
docker tag $IMAGE_NAME $IMAGE_PATH/$IMAGE_NAME
docker push $IMAGE_PATH/$IMAGE_NAME

