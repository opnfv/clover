.. This work is licensed under a Creative Commons Attribution 4.0 International License.
.. http://creativecommons.org/licenses/by/4.0
.. SPDX-License-Identifier CC-BY-4.0
.. (c) Authors of Clover

.. _modsecurity_config_guide:

=========================================
ModSecurity Configuration Guide
=========================================

This document provides a guide to setup the ModSecurity web application firewall
as a security enhancement for the Istio ingressgateway.


ModSecurity Overview
=====================

ModSecurity is an open source web application firewall. Essentially, ModSecurity
is an Apache module that can be added to any compatible version of Apache. To
detect threats, the ModSecurity engine is usually deployed embedded within the
webserver or as a proxy server in front of a web application. This allows the
engine to scan incoming and outgoing HTTP communications to the endpoint.

In Clover, we deploy ModSecurity on an Apache server and running it as a
Kubernetes service that reside in "clover-gateway" namespace.

ModSecurity provides very little protection on its own. In order to become
useful, ModSecurity must be configured with rules. Dependent on the rule
configuration the engine will decide how communications should be handled which
includes the capability to pass, drop, redirect, return a given status code,
execute a user script, and more.

In Clover, we choose the OWASP ModSecurity Core Rule Set (CRS) for use with
ModSecurity.

The OWASP ModSecurity Core Rule Set (CRS) is a set of generic attack detection
rules. The CRS aims to protect web applications from a wide range of attacks,
including the OWASP Top Ten, with a minimum of false alerts.


Ingress traffic security enhancement
======================================

In a typical Istio service mesh, ingressgateway terminates TLS from external
networks and allows traffic into the mesh.

.. image:: imgs/istio_gateway.png
    :align: center
    :scale: 100%

Clover enhances the security aspect of ingressgateway by redirecting all incoming
HTTP requests through the ModSecurity WAF. To redirect HTTP traffic to the ModSecurity,
Clover enables ext_authz (external authorization) Envoy filter on the ingressgateway.

For all incoming HTTP traffic, the ext_authz filter will authenticate each ingress
request with the ModSecurity service. To perform authentication, an HTTP subrequest
is sent from ingressgateway to ModSecurity where the subrequest is verified. If
the subrequest is clean, ModSecurity will return a 2xx response code, access is
allowed; If it returns 401 or 403, access is denied.


Deploying the ModSecurity WAF
==============================

.. _modsecurity_prerequisites:

Prerequisites
-------------

The following assumptions must be met before continuing on to deployment:

 * Installation of Kubernetes has already been performed.
 * Installation of Istio and Istio client (istioctl) is in your PATH.

Deploy from source
------------------

Clone the Clover git repository and navigate within the samples directory as
shown below:

.. code-block:: bash

    $ git clone https://gerrit.opnfv.org/gerrit/clover
    $ cd clover/samples/scenarios
    $ git checkout stable/gambia

To deploy the ModSecurity WAF in the "clover-gateway" Kubernetes namespace, use
the following command:

.. code-block:: bash

    $ kubectl create namespace clover-gateway
    $ kubectl apply -n clover-gateway -f modsecurity_all_in_one.yaml

Verifying the deployment
------------------------

To verify the ModSecurity pod is deployed, executing the command below:

.. code-block:: bash

    $ kubectl get pod -n clover-gateway

The listing below must include the following ModSecurity pod:

.. code-block:: bash

    $ NAME                                        READY     STATUS      RESTARTS   AGE
    modsecurity-crs-cf5fffcc-whwqm                1/1       Running     0          1d

To verify the ModSecurity service is created, executing the command below:

.. code-block:: bash

    $ kubectl get svc -n clover-gateway

The listing below must include the following ModSecurity service:

.. code-block:: bash

    $ NAME                     TYPE           CLUSTER-IP      EXTERNAL-IP   PORT(S)         AGE
    modsecurity-crs            NodePort       10.233.11.72    <none>        80:31346/TCP    1d

To verify the ext-authz Envoy filter is created, executing the command below:

.. code-block:: bash

    $ istioctl get envoyfilter -n clover-gateway

The listing below must include the following Envoy filter:

.. code-block:: bash

    $ NAME        KIND                                       NAMESPACE      AGE
    ext-authz   EnvoyFilter.networking.istio.io.v1alpha3     istio-system   1d


ModSecurity configuration
==========================

OWASP ModSecurity CRS mode
---------------------------

The OWASP ModSecurity CRS can run in two modes:

* **Anomaly Scoring Mode** - In this mode, each matching rule increases an
'anomaly score'. At the conclusion of the inbound rules, and again at the
conclusion of the outbound rules, the anomaly score is checked, and the blocking
evaluation rules apply a disruptive action, by default returning an error 403.

* **Self-Contained Mode** - In this mode, rules apply an action instantly. Rules
inherit the disruptive action that you specify (i.e. deny, drop, etc). The first
rule that matches will execute this action. In most cases this will cause evaluation
to stop after the first rule has matched, similar to how many IDSs function.

By default, the CRS runs in Anomally scoring mode.

You can configurate CRS mode by editing the **crs-setup.conf** in the modsecurity-crs container:

.. code-block:: bash

    $ kubectl exec -t -i -n clover-gateway [modsecurity-crs-pod-name] -c modsecurity-crs -- bash
    $ vi /etc/apache2/modsecurity.d/owasp-crs/crs-setup.conf

Alert logging
-------------

By default, CRS enables all detailed logging to the ModSecurity audit log.
You can check the audit log using the command below:

.. code-block:: bash

    $ kubectl exec -t -i -n clover-gateway [modsecurity-crs-pod-name] -c modsecurity-crs -- cat /var/log/modsec_audit.log
