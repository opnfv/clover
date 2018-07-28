# Copyright (c) Authors of Clover
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0

FROM java:8

RUN wget http://apache.mirrors.hoobly.com//jmeter/binaries/apache-jmeter-4.0.tgz
RUN tar -xvzf apache-jmeter-4.0.tgz
RUN rm apache-jmeter-4.0.tgz
RUN mv apache-jmeter-4.0 /jmeter
ENV JMETER_HOME /jmeter
ENV PATH $JMETER_HOME/bin:$PATH
COPY rmi_keystore.jks $JMETER_HOME/bin

RUN apt update && apt install -y python-setuptools python-dev python-pip
RUN python -m pip install --upgrade pip
RUN python -m pip install enum34 futures cython
RUN python -m pip install grpcio protobuf jinja2

WORKDIR /jmeter/bin

COPY jmeter-master/process process
COPY jmeter-master/grpc grpc
COPY jmeter-master/tests tests

CMD ./process/grpc_process.sh no_init
