# Copyright (c) Authors of Clover
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0

FROM ubuntu:16.04
LABEL maintainer="Eddie Arrage" maintainer_email="eddie.arrage@huawei.com"
LABEL version="0.1" description="Clover - Nginx HTTP Proxy"

RUN \
    apt-get update && apt-get install -y \
# Some debug tools in container
    wget \
    libdnet \
    net-tools \
# Nginx as proxy
    nginx \
    python-pip \
&& \
# Install required python packages
    python -m pip install grpcio redis jinja2

COPY /process /process
COPY /grpc /grpc
CMD ./process/start_process.sh proxy
