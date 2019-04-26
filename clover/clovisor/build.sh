# Copyright (c) Authors of Clover
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0

GOVERSION=1.12
OS=linux
ARCH=amd64
GOPATH=/home/s3wong/go
GOLANGUNIXVERSION=release-branch.go1.11
CLIENTGOVERSION=v10.0.0

SRCDIR=`pwd`

wget https://dl.google.com/go/go$GOVERSION.$OS-$ARCH.tar.gz
sudo tar -C /usr/local -xzf go$GOVERSION.$OS-$ARCH.tar.gz
export PATH=$PATH:/usr/local/go/bin
export PATH=$GOPATH/bin:$PATH

sudo apt install -y gcc
sudo apt-key adv --keyserver keyserver.ubuntu.com --recv-keys D4284CDD
echo "deb https://repo.iovisor.org/apt/bionic bionic main" | sudo tee /etc/apt/sources.list.d/iovisor.list
sudo apt-get update -y
sudo apt-get install -y bcc-tools libbcc-examples linux-headers-$(uname -r)

go get github.com/google/gopacket
go get github.com/iovisor/gobpf
go get github.com/opentracing/opentracing-go
go get github.com/pkg/errors
go get github.com/go-redis/redis
go get github.com/uber/jaeger-client-go
go get github.com/vishvananda/netlink
go get github.com/vishvananda/netns
go get golang.org/x/sys/unix
cd $GOPATH/src/golang.org/x/sys/unix
git checkout $GOLANGUNIXVERSION

go get github.com/tools/godep
go get k8s.io/client-go/...
cd $GOPATH/src/k8s.io/client-go
git checkout $CLIENTGOVERSION
godep restore ./...

#cd $SRCDIR/libclovisor
#go build .
#cd ../
#go build -o clovisor .
