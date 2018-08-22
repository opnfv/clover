# Copyright (c) Authors of Clover
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
from halyard import Halyard

test = Halyard()

# please install the spinnaker useing the spinnaker/install/install.yml first

print  "######## add docker provider ##########"
address = "https://index.docker.io"
repositories = ['opnfv/clover-ns-nginx-proxy', 'opnfv/clover-ns-nginx-server', 'library/nginx']
add_docker = test.add_docker_account(address, "my-docker-registry", repositories)
print  "######## result ##########"
print add_docker

# When add k8s, you need a K8s cluster and its credentials. for example "/root/.kube/config"
print  "######## add kubernetes provider ##########"
add_k8s = test.add_k8s_account('my-k8s-v1-t1156', "/root/.kube/config", "V1", ['my-docker-registry'])
print  "######## result ##########"
print add_k8s

print  "######## k8s account list ##########"
k8s_list = test.list_accounts('kubernetes')
print  "####### result ##########"
print k8s_list

print  "######## docker account list ##########"
docker_list = test.list_accounts('dockerRegistry')
print  "####### result ##########"
print docker_list

print  "######## delete kubernetes provider ##########"
del_k8s = test.delete_account('kubernetes','my-k8s-v1-t115')
print  "######## result ##########"
print del_k8s

print  "######## delete docker registry provider ##########"
del_docker = test.delete_account('dockerRegistry','my-docker-registry')
print  "######## result ##########"
print del_docker
