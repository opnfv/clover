# Copyright (c) Authors of Clover
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0

FROM opnfv/clover

ENV REPOS_DIR="/home/opnfv/repos"

# Clover repo
ENV CLOVER_REPO_DIR="${REPOS_DIR}/clover"

# Install required python packages
RUN python -m pip install cassandra-driver redis

# Set work directory
WORKDIR ${CLOVER_REPO_DIR}

COPY /process clover/collector/process
COPY /grpc clover/collector/grpc
COPY /db clover/collector/db
COPY __init__.py clover/collector/__init__.py

RUN pip install .

WORKDIR "${CLOVER_REPO_DIR}/clover/collector"

CMD ./process/grpc_process.sh no_schema_init
