#!/bin/bash
#
# Copyright (c) Authors of Clover
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
#

docker build -f subservices/server/Dockerfile -t http-server .
docker tag http-server localhost:5000/http-server
docker push localhost:5000/http-server
