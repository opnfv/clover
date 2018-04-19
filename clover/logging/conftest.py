# Copyright (c) Authors of Clover
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0

from elasticsearch import Elasticsearch
import pytest

ES_HOST="localhost:9200"

@pytest.fixture
def es():
    return Elasticsearch([ES_HOST])
