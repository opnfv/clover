# Copyright (c) Authors of Clover
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0

FROM fedora:27 
# Use fedora base for snort
LABEL maintainer="Eddie Arrage" maintainer_email="eddie.arrage@huawei.com"
LABEL version="0.1" description="Clover - Snort IDS / Content Inspect Service"

RUN \
    yum update -y \
&& \
    yum install -y \
# Core snort install elements
    https://www.snort.org/downloads/snort/daq-2.0.6-1.f21.x86_64.rpm \
    https://www.snort.org/downloads/snort/snort-2.9.11.1-1.f25.x86_64.rpm \
# Debug packages that aren't required for normal operation
    wget libdnet net-tools iputils procps \
    python-pip \
# For snort to process inbound http client traffic, install nginx server
    nginx \
    ldconfig \
&& \
    mkdir -p /etc/snort/rules \
&& \
    mkdir /usr/local/lib/snort_dynamicrules \
&& \
    chmod -R 5775 /etc/snort \
&& \
    chmod -R 5775 /var/log/snort \
&& \
    chmod -R 5775 /usr/local/lib/snort_dynamicrules \
&& \
    chown -R snort:snort /etc/snort \
&& \
    chown -R snort:snort /var/log/snort \
&& \
    chown -R snort:snort /usr/local/lib/snort_dynamicrules \
&& \
    touch /etc/snort/rules/white_list.rules \
&& \
    touch /etc/snort/rules/black_list.rules \
&& \
    touch /etc/snort/rules/local.rules \
# Install snort community rules for now
&& \
    wget https://www.snort.org/rules/community -O ~/community.tar.gz \
&& \
    tar -xvf ~/community.tar.gz -C ~/ \
&& \
    cp ~/community-rules/* /etc/snort/rules \
&& \
# Modify snort.conf file
    sed -i 's/include \$RULE\_PATH/#include \$RULE\_PATH/' /etc/snort/snort.conf \
&& \
    sed -i 's/var WHITE\_LIST\_PATH \.\.\/rules/var WHITE\_LIST\_PATH \/etc\/snort\/rules/' /etc/snort/snort.conf \
&& \
    sed -i 's/var BLACK\_LIST\_PATH \.\.\/rules/var BLACK\_LIST\_PATH \/etc\/snort\/rules/' /etc/snort/snort.conf \
&& \
    sed -i 's/\# output unified2\: filename merged\.log, limit 128, nostamp, mpls\_event\_types, vlan\_event\_types/output unified2\: filename snort\.log, limit 128/' /etc/snort/snort.conf \
&& \
    sed -i 's/\#include \$RULE\_PATH\/local\.rules/include \$RULE\_PATH\/local\.rules\ninclude \$RULE\_PATH\/community\.rules/' /etc/snort/snort.conf \
&& \
    cd /usr/lib64 \
&& \
# Account for libdnet issue
    ln -s libdnet.so.1.0.1 libdnet.1 \
&& \
# Install required python libraries
    python -m pip install grpcio redis idstools

COPY /process /process
COPY /grpc /grpc
CMD ./process/start_process.sh
