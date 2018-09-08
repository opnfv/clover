# Copyright (c) Authors of Clover
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0

FROM ubuntu:16.04
LABEL maintainer="Eddie Arrage" maintainer_email="eddie.arrage@huawei.com"
LABEL version="0.2" description="Clover - Nginx HTTP Server"

RUN \
    apt-get update && apt-get install -y \
# Some debug tools in container
    wget \
    libdnet \
    net-tools \
# Packages required to build nginx from source
    build-essential \
    libpcre3-dev \
    libpcre3++-dev \
    libgeoip-dev \
    libxslt-dev \
    git \
# Install required python packages
    python-pip \
&& \
    python -m pip install grpcio redis jinja2 protobuf psutil \
&& \
# Get nginx and module add-on source
    wget https://nginx.org/download/nginx-1.15.0.tar.gz && tar zxvf nginx-1.15.0.tar.gz \
&& \
    wget https://ftp.pcre.org/pub/pcre/pcre-8.42.tar.gz && tar xzvf pcre-8.42.tar.gz \
&& \
    wget http://www.zlib.net/zlib-1.2.11.tar.gz && tar xzvf zlib-1.2.11.tar.gz \
&& \
    wget https://www.openssl.org/source/openssl-1.1.0f.tar.gz && tar xzvf openssl-1.1.0f.tar.gz \
&& \
    git clone https://github.com/Austinb/nginx-upload-module.git \
&& \
    wget https://github.com/arut/nginx-rtmp-module/archive/v1.2.1.tar.gz && tar xzvf v1.2.1.tar.gz
RUN rm -rf *.tar.gz

# Build supporting modules
ENV  LDFLAGS -fPIC
WORKDIR /pcre-8.42
RUN ./configure
RUN make
RUN make install

WORKDIR /zlib-1.2.11
RUN ./configure
RUN make
RUN make install

WORKDIR /openssl-1.1.0f
RUN ./config
RUN make
RUN make install

WORKDIR /nginx-1.15.0

# Build nginx with all modules in stock Ubuntu 16.04 version
# Add upload and rtmp modules
RUN ./configure \
    --prefix=/usr/share/nginx \
    --http-fastcgi-temp-path=/var/lib/nginx/fastcgi \
    --http-scgi-temp-path=/var/lib/nginx/scgi \
    --sbin-path=/usr/sbin/nginx \
    --conf-path=/etc/nginx/nginx.conf \
    --error-log-path=/var/log/nginx/error.log \
    --http-log-path=/var/log/nginx/access.log \
    --pid-path=/run/nginx.pid \
    --lock-path=/var/lock/nginx.lock \
    --with-pcre=../pcre-8.42 \
    --with-pcre-jit \
    --with-ipv6 \
    --with-http_stub_status_module \
    # --with-http_image_filter_module \
    --with-http_xslt_module \
    --with-mail \
    --with-zlib=../zlib-1.2.11 \
    --with-openssl=../openssl-1.1.0f \
    --with-openssl-opt=enable-ec_nistp_64_gcc_128 \
    --with-openssl-opt=no-nextprotoneg \
    --with-openssl-opt=no-weak-ssl-ciphers \
    --with-openssl-opt=no-ssl3 \
    --with-http_ssl_module \
    --with-stream \
    --with-stream_ssl_module \
    --with-threads \
    --with-mail=dynamic \
    --with-mail_ssl_module \
    --http-client-body-temp-path=/var/lib/nginx/body \
    --http-proxy-temp-path=/var/lib/nginx/proxy \
    --with-http_realip_module \
    --with-http_geoip_module \
    --http-uwsgi-temp-path=/var/lib/nginx/uwsgi \
    --with-http_v2_module \
    --with-http_sub_module \
    --with-http_addition_module \
    --with-http_dav_module \
    --with-http_auth_request_module \
    --with-http_gunzip_module \
    --with-http_gzip_static_module \
    --with-debug \
    --add-module=../nginx-upload-module \
    --add-module=../nginx-rtmp-module-1.2.1

RUN make
RUN make install

WORKDIR /
RUN mkdir /var/lib/nginx
RUN mkdir /var/www
RUN mkdir /var/www/html

COPY /process /process
COPY /grpc /grpc
CMD ./process/start_process.sh server
