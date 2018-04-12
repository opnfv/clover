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

# Get latest istio version, refer: https://git.io/getLatestIstio
if [ "x${ISTIO_VERSION}" = "x" ] ; then
  ISTIO_VERSION=$(curl -L -s https://api.github.com/repos/istio/istio/releases/latest | \
                  grep tag_name | sed "s/ *\"tag_name\": *\"\(.*\)\",*/\1/")
fi

mkdir istio-source

curl -L https://github.com/istio/istio/releases/download/${ISTIO_VERSION}/istio-${ISTIO_VERSION}-linux.tar.gz | \
tar xz -C istio-source --strip-components 1

# Install istioctl
cp istio-source/bin/* /usr/local/bin

# Install kubectl
curl -s http://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key add -
cat << EOF > /etc/apt/sources.list.d/kubernetes.list
deb http://apt.kubernetes.io/ kubernetes-xenial main
EOF

apt-get update \
    && apt-get install -y --allow-downgrades kubectl=1.9.1-00 \
    && apt-get -y autoremove \
    && apt-get clean

# Enable kubectl bash completion
echo "source <(kubectl completion bash)" >> ~/.bashrc
