# Copyright (c) Authors of Clover
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0

FROM ubuntu:16.04

RUN apt-get update && apt-get install -y \
    nginx \
    python-pip \
    git \
    python-dev

# Install required python packages
RUN python -m pip install gunicorn flask \
    grpcio protobuf jinja2 redis requests

COPY /control /control
COPY /process /process

COPY process/nginx.conf /etc/nginx/nginx.conf

# Get all grpc files
RUN mkdir  /grpc_temp
WORKDIR /grpc_temp
RUN git config --global http.sslVerify false
RUN git clone https://github.com/opnfv/clover.git
RUN cp clover/samples/services/snort_ids/docker/grpc/snort_pb2_grpc.py /control/api
RUN cp clover/samples/services/snort_ids/docker/grpc/snort_pb2.py /control/api
RUN cp clover/samples/services/nginx/docker/grpc/nginx_pb2_grpc.py /control/api
RUN cp clover/samples/services/nginx/docker/grpc/nginx_pb2.py /control/api
RUN cp clover/clover/collector/grpc/collector_pb2_grpc.py /control/api
RUN cp clover/clover/collector/grpc/collector_pb2.py /control/api
RUN cp clover/clover/tools/jmeter/jmeter-master/grpc/jmeter_pb2_grpc.py /control/api
RUN cp clover/clover/tools/jmeter/jmeter-master/grpc/jmeter_pb2.py /control/api
RUN cp -rf  clover/clover/spinnaker/lib/ /control/api
RUN rm -rf /grpc_temp

WORKDIR /process
CMD ./start_process.sh
