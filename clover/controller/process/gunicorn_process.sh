#!/bin/bash
#
# Copyright (c) Authors of Clover
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
#

# it take a long time to add kubernetes. So I increse the timeout
# and workers

gunicorn --bind 0.0.0.0:8000 -t 1200 -w 5 --chdir /control wsgi
