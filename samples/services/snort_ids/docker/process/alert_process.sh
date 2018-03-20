#!/bin/bash
#
# Copyright (c) Authors of Clover
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
#

# start nginx server to handle incoming http requests
/usr/sbin/nginx &

# Process snort alerts
python grpc/snort_alerts.py

