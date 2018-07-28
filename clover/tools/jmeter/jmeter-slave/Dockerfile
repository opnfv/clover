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
RUN mkdir /share
COPY rmi_keystore.jks $JMETER_HOME/bin

WORKDIR $JMETER_HOME
# Ports to be exposed from the container for JMeter Master
RUN mkdir scripts

EXPOSE 1099

WORKDIR /jmeter/bin

CMD ./jmeter-server
