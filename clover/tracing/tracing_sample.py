# Copyright (c) Authors of Clover
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0

import uuid
import time

from clover.tracing.tracing import Tracing

t = Tracing('localhost', '30888')

# Get toplevel services stored in tracing
services = t.getServices()
print(services)

# Get traces from the last hour for istio-ingress service
service = 'istio-ingress'
traces = t.getTraces(service, 3600)
# Get process names for first trace service
t.outProcesses(traces)

# Turn off redis tracing store and output basic trace info
t.use_redis = False
t.outTraces(traces)

# Setup basic test and store in redis
t.use_redis = True
t.setTest(uuid.uuid4())
time.sleep(20)
# Get all traces from test start time when time_back=0
traces = t.getTraces(service, 0)
# Store traces in redis
t.outTraces(traces)

# Get test id for some number of tests back
testid = t.getRedisTestid('0')
print(testid)
traceids = t.getRedisTraceids(testid)
print(traceids)

# Print out span and tag info for all traces in test
# Will continue to consider what to extract from hashes for e2e validation
t.getRedisTestAll(testid)

# t.monitorTraces(1)
