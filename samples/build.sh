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

CLOVER_BASE_DIR=`cd ${BASH_SOURCE[0]%/*}/..;pwd`
export IMAGE_PATH=opnfv

cd $CLOVER_BASE_DIR/samples/services/nginx/docker/

./build_lb.sh
./build_proxy.sh
./build_server.sh

cd $CLOVER_BASE_DIR/samples/services/snort_ids/docker/
./build.sh

echo "Clover sample build complete!"
