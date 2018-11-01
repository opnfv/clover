#!/bin/bash
#
# Copyright (c) Authors of Clover
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
#

IMAGE_NAME=${IMAGE_NAME:-"clover-spark:latest"}
IMAGE_PATH=${IMAGE_PATH:-"localhost:5000"}
CLASS_NAME=${CLASS_NAME:-"CloverFast"}
JAR_NAME=${JAR_NAME:-"clover-spark_2.11-1.0.jar"}

bin/spark-submit \
  --master k8s://https://kubernetes.default.svc \
  --deploy-mode cluster \
  --name "clover-spark-fast" \
  --class $CLASS_NAME \
  --conf spark.executor.instances=2 \
  --conf spark.kubernetes.container.image="$IMAGE_PATH/$IMAGE_NAME" \
  --conf spark.kubernetes.authenticate.driver.serviceAccountName="clover-spark" \
  --conf spark.kubernetes.namespace="clover-system" \
  --jars local:///opt/spark/jars/redisclient_2.11-3.7.jar,local:///opt/spark/jars/datastax_spark-cassandra-connector-2.3.0-s_2.11.jar \
  local:///opt/spark/jars/$JAR_NAME
