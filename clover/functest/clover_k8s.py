# Copyright (c) Authors of Clover
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0

import functest_kubernetes.k8stest as k8stest

import clover.servicemesh.validate as istio_validate

class K8sCloverTest(k8stest.K8sTesting):
    """Clover test suite"""

    def __init__(self, **kwargs):
        if "case_name" not in kwargs:
            kwargs.get("case_name", 'clover_k8s')
        super(K8sCloverTest, self).__init__(**kwargs)
        self.check_envs()

    def run_kubetest(self):
        success = istio_validate.validateDeploy()
        if success:
            self.result = 100
        else:
            self.result = 0

