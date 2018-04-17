# Copyright (c) Authors of Clover
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0

FROM ubuntu:16.04
LABEL image=opnfv/clover
ARG ISTIO_VERSION=0.6.0

# GIT repo directory
ENV REPOS_DIR="/home/opnfv/repos"

# Clover repo
ENV CLOVER_REPO_DIR="${REPOS_DIR}/clover"

# Install basic dependency
RUN apt-get update \
    && apt-get install -y git python-setuptools python-pip curl apt-transport-https \
    && apt-get -y autoremove && apt-get clean \
    && pip install --upgrade pip \
    && python -m pip install grpcio argparse

# Fetch source code
RUN mkdir -p ${REPOS_DIR}
COPY ./ ${CLOVER_REPO_DIR}

# Install tools like istioctl & kubectl
RUN ${CLOVER_REPO_DIR}/docker/setup.sh

# Install clover package
RUN cd ${CLOVER_REPO_DIR} && pip install ./

# Set work directory
WORKDIR ${CLOVER_REPO_DIR}
