FROM ubuntu:18.04

ARG TARGET_KERNEL_VER

RUN set -ex; \
  echo "deb [trusted=yes] http://repo.iovisor.org/apt/bionic bionic main" > /etc/apt/sources.list.d/iovisor.list; \
  apt-get update -y; \
  DEBIAN_FRONTEND=noninteractive apt-get install -y \
    auditd \
    bcc-tools \
    linux-headers-$TARGET_KERNEL_VER \
    libelf1;

COPY . .
RUN chmod +x clovisor

CMD ["./clovisor"]
