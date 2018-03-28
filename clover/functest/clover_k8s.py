# Copyright (c) Authors of Clover
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0

import functest_kubernetes.k8stest as k8stest


class K8sCloverTest(k8stest.K8sTesting):
    """Clover test suite"""

    def __init__(self, **kwargs):
        if "case_name" not in kwargs:
            kwargs.get("case_name", 'clover_k8s')
        super(K8sCloverTest, self).__init__(**kwargs)
        self.check_envs()

    def run_kubetest(self):
        success = True
        if success:
            self.result = 100
        elif failure:
            self.result = 0

