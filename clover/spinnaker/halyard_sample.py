# Copyright (c) Authors of Clover
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0

import halyard


# please install the spinnaker useing the spinnaker/install/quick-install-spinnaker.yml first
print  "######## add docker provider ##########"
address = "https://index.docker.io"
repositories = ['wtwde/onap', 'wtwde/spinnaker', 'library/nginx']
add_docker = halyard.add_docker_account(address, "docker-test", repositories)
print  "######## result ##########"
print add_docker

print  "######## add kubernetes provider ##########"
add_k8s = halyard.add_k8s_account('my-k8s-v1-t11561', "/root/config.115", "V1", ['dockerhub'])
print  "######## result ##########"
print add_k8s

print  "######## k8s account list ##########"
k8s_list = halyard.list_accounts('kubernetes')
print  "####### result ##########"
print k8s_list

print  "######## docker account list ##########"
docker_list = halyard.list_accounts('dockerRegistry')
print  "####### result ##########"
print docker_list

print  "######## delete kubernetes provider ##########"
del_k8s = halyard.delete_account('kubernetes','my-k8s-v1-t11561')
print  "######## result ##########"

print  "######## delete docker registry provider ##########"
del_docker = halyard.delete_account('dockerRegistry','docker-test')
print  "######## result ##########"
print del_docker
