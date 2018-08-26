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

SAMPLE_APP_DIR=$(cd $(dirname ${BASH_SOURCE[0]})/..;pwd)
CONTAINER_IMAGE_NAME="opnfv/clover-sample-app"
CONTAINER_NAME="sample-app"
CONTAINER_PORT="8080"
IMAGE_VERSION="latest"
BACKEND_ENV_ARGS="-e VERSION=${IMAGE_VERSION} -e COMPONENT=backend"
FRONTEND_ENV_ARGS="-e VERSION=${IMAGE_VERSION} -e COMPONENT=frontend"

sample_app_cleanup() {
  docker stop "${CONTAINER_NAME}-frontend"
  docker stop "${CONTAINER_NAME}-backend"
  docker rm -f  "${CONTAINER_NAME}-frontend"
  docker rm -f  "${CONTAINER_NAME}-backend"
  docker image rm ${CONTAINER_IMAGE_NAME}:latest
}

sample_app_verify()
{
  pushd "${SAMPLE_APP_DIR}"

  docker build -t ${CONTAINER_IMAGE_NAME}:latest \
               -f ./docker/Dockerfile ./docker/
  docker run -d --expose 8080 ${BACKEND_ENV_ARGS} \
             --name "${CONTAINER_NAME}-backend" \
             ${CONTAINER_IMAGE_NAME}:latest \
             /bin/sh -c ./gke-info

  BACKEND_URL=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' \
                ${CONTAINER_NAME}-backend)
  FRONTEND_ENV_ARGS="${FRONTEND_ENV_ARGS} -e BACKEND_URL=http://${BACKEND_URL}:8080/metadata"

  docker run -d --expose 8080 -p 8080 ${FRONTEND_ENV_ARGS} \
             --name "${CONTAINER_NAME}-frontend" \
             ${CONTAINER_IMAGE_NAME}:latest \
             /bin/sh -c ./gke-info

  HOST_CONTAINER_PORT=$(docker inspect -f \
                       '{{ (index (index .NetworkSettings.Ports "8080/tcp") 0).HostPort }}' \
                       "${CONTAINER_NAME}-frontend")

  CODE=$(timeout 10s curl -IXGET -so /dev/null -w "%{http_code}" \
         localhost:${HOST_CONTAINER_PORT})

  if [[ ${CODE} -eq "200" ]]; then
    echo "Image is ready to be pushed!"
  else
    echo "Connection to container port failed, image is not ready!"
    exit 1
  fi
}
