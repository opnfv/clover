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

ISTIO_DIR_NAME="istio-$ISTIO_VERSION"

cd /usr/local/
curl -L https://git.io/getLatestIstio | sh -
mv $ISTIO_DIR_NAME istio-source

# Install kubectl
curl -s http://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key add -
cat << EOF > /etc/apt/sources.list.d/kubernetes.list
deb http://apt.kubernetes.io/ kubernetes-xenial main
EOF

apt-get update \
    && apt-get install -y --allow-downgrades kubectl=1.9.1-00 \
    && apt-get -y autoremove \
    && apt-get clean

# Persistently append istioctl bin path to PATH env
echo 'export PATH="$PATH:/usr/local/istio-source/bin"' >> ~/.bashrc
echo "source <(kubectl completion bash)" >> ~/.bashrc
