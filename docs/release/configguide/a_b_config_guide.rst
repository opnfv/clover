.. This work is licensed under a Creative Commons Attribution 4.0 International License.
.. http://creativecommons.org/licenses/by/4.0
.. SPDX-License-Identifier CC-BY-4.0
.. (c) Authors of Clover

.. _a_b_config_guide:

=========================================
A-B Sample Validation Configuration Guide
=========================================

Istio supports the ability to have multiple service versions, which allows for use-cases
such as staging services and moving to production when newer versions are vetted. Multiple variants
of a service can run in parallel and Istio can perform request routing between the variants
using configured route rules.

This script sets up route rules between the two load balancer versions (http-lb-v1/v2) in the
Service Delivery Controller (SDC) sample to modify the ratio of incoming request traffic to send
to each. It then employs the overall request/response times obtained from the tracing module to
validate the response time performance of v2 is within 120% of v1. The 120% condition can be
configured in an input configuration yaml.

Using the sample script
=======================

Prerequisites
-------------

The following assumptions must be met before executing the sample script:

 * The prerequisites stipulated at :ref:`sdc_prerequisites` are considered. The use of flannel
   as the CNI network add-on is required.
 * Ensure the SDC sample is deployed. The easiest way to accomplish this is using the Clover
   container outlined in the SDC guide at :ref:`sdc_deploy_container`.
 * Deploy Jaeger tracing and determine the tracing port. The instructions in the SDC guide
   at :ref:`sdc_view_container` can be used for this purpose. The exposed tracing port is
   required as the ``-p`` argument in the script.
 * The http-lb-v2 in the SDC sample is load balancing across clover-server4/5 using the
   command outlined at :ref:`sdc_modify_lb`
 * Ensure Istio is in the path by downloading Istio separately into a directory with the
   commands below:

.. code-block:: bash

    $ curl -L https://github.com/istio/istio/releases/download/0.6.0/istio-0.6.0-linux.tar.gz | tar xz
    $ cd istio-0.6.0
    $ export PATH=$PWD/bin:$PATH

Environment setup
------------------

First setup the environment using the Clover source with the following commands:

.. code-block:: bash

    $ git clone https://gerrit.opnfv.org/gerrit/clover
    $ cd clover
    $ pip install .
    $ git checkout stable/fraser
    $ cd clover

Edit the input configuration yaml file located at ``test/yaml/fraser_a_b_test.yaml``
and modify the value under the ``params`` key with the istio-ingress port obtained using
the SDC guide at :ref:`sdc_ingress_port`. The example of port 32580 is shown below in bold.

.. code-block:: bash

    traffic-test:
      name: lb-test.sh
      params:
        - 10.244.0.1
        - **32580**

Execute toplevel script
-----------------------

To execute the script, use the command:

.. code-block:: bash
    $ python test/fraser_a_b_test.py -t test/yaml/fraser_a_b_test.yaml -p 30869

The value to the argument ``-p`` must be the tracing port exposed outside of the Kubernetes
cluster.

Results
-------

The script uses ``wget`` to make twenty HTTP GET requests to the SDC sample. It fetches the
total response time for the service mesh to respond to requests using the Clover tracing module
and calculates and average. The script will pass if performance of http-lb-v2 has response times
within 120% of v1 and fail otherwise.

Troubleshooting
===============

If the script fails because a route rule with the same name exists from a
previous test run, use the following command to delete the rule before executing the
sample script::

    istioctl -n default delete routerules lb-default

