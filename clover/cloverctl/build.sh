# Copyright (c) Authors of Clover
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0

GOVERSION=1.10.3
OS=linux
ARCH=amd64
GOPATH=/home/ubuntu/go
CLIENTGOVERSION=v8.0.0

# Install go on Ubuntu 16.04

wget https://dl.google.com/go/go$GOVERSION.$OS-$ARCH.tar.gz
sudo tar -C /usr/local -xzf go$GOVERSION.$OS-$ARCH.tar.gz
export PATH=$PATH:/usr/local/go/bin
export PATH=$GOPATH/bin:$PATH

# Get dependencies

go get github.com/ghodss/yaml
go get github.com/tools/godep
go get -u github.com/spf13/cobra/cobra
go get -u gopkg.in/resty.v1

go get k8s.io/apimachinery/pkg/runtime
go get k8s.io/client-go/...
cd $GOPATH/src/k8s.io/client-go
git checkout $CLIENTGOVERSION
godep restore ./...
rm -rf vendor/

# Build cloverctl

go install cloverctl
