# Copyright (c) Authors of Clover
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0

FROM java:8

RUN mkdir /spark
WORKDIR /spark
RUN wget https://archive.apache.org/dist/spark/spark-2.3.2/spark-2.3.2-bin-hadoop2.7.tgz
# COPY spark-2.3.2-bin-hadoop2.7.tgz /spark
RUN tar -xvzf spark-2.3.2-bin-hadoop2.7.tgz

COPY runner.sh /spark/spark-2.3.2-bin-hadoop2.7
COPY runner_fast.sh /spark/spark-2.3.2-bin-hadoop2.7
WORKDIR /spark/spark-2.3.2-bin-hadoop2.7

RUN curl -LO https://storage.googleapis.com/kubernetes-release/release/$(curl -s https://storage.googleapis.com/kubernetes-release/release/stable.txt)/bin/linux/amd64/kubectl
RUN chmod +x ./kubectl

CMD ./runner.sh
