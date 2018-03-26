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
CLOVER_WORK_DIR=$CLOVER_BASE_DIR/work
export IMAGE_PATH=opnfv
export IMAGE_TAG=latest

mkdir -p $CLOVER_WORK_DIR/samples

function render_config() {
    for f in $(ls); do
        sed -e "s/{{IMAGE_PATH}}/$IMAGE_PATH/g" \
            -e "s/{{IMAGE_TAG}}/$IMAGE_TAG/g" \
            $f > $CLOVER_WORK_DIR/samples/$f
    done
}

for svc in nginx snort_ids; do
    cd $CLOVER_BASE_DIR/samples/services/$svc/yaml
    render_config
done

echo "Clover generate sample services config complete!"
