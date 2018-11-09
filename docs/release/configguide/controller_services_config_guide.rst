.. This work is licensed under a Creative Commons Attribution 4.0 International License.
.. http://creativecommons.org/licenses/by/4.0
.. SPDX-License-Identifier CC-BY-4.0
.. (c) Authors of Clover

.. _controller_services_config_guide:

==============================================
Clover Controller Services Configuration Guide
==============================================

This document provides a guide to use the Clover controller services, which are introduced in
the Clover Gambia release.

Overview
=========

Clover controller services allow users to control and access information about Clover
microservices. Two new components are added to Clover to facilitate an ephemeral, cloud native
workflow. A CLI interface with the name **cloverctl** interfaces to the Kubernetes (k8s)
API and also to **clover-controller**, a microservice deployed within the k8s cluster to
instrument other Clover k8s services including sample network services, visibility/validation
services and supporting datastores (redis, cassandra). The **clover-controller** service
provides message routing communicating REST with cloverctl or other API/UI interfaces and
gRPC to internal k8s cluster microservices. It acts as an internal agent and reduces the need
to expose multiple Clover services outside of a k8s cluster.

The **clover-controller** is packaged as a docker container with manifests to deploy
in a Kubernetes (k8s) cluster. The **cloverctl** CLI is packaged as a binary (Golang) within a
tarball with associated yaml files that can be used to configure and control other Clover
microservices within the k8s cluster via **clover-controller**. The **cloverctl** CLI can also
deploy/delete other Clover services within the k8s cluster for convenience.

The **clover-controller** service provides the following functions:

 * **REST API:** interface allows CI scripts/automation to control sample network sample services,
   visibility and validation services. Analyzed visibility data can be consumed by other
   services with REST messaging.

 * **CLI Endpoint:** acts as an endpoint for many **cloverctl** CLI commands using the
   **clover-controller** REST API and relays messages to other services via gRPC.

 * **UI Dashboard:** provides a web interface exposing visibility views to interact with
   Clover visibility services. It presents analyzed visibility data and provides basic controls
   such as selecting which user services visibility will track.

.. image:: imgs/controller_services.png
    :align: center
    :scale: 100%

The **cloverctl** CLI command syntax is similar to k8s kubectl or istio istioctl CLI tools, using
a <verb> <noun> convention.

Help can be accessed using the ``--help`` option, as shown below::

    $ cloverctl --help

Deploying Clover system services
================================

Prerequisites
-------------

The following assumptions must be met before continuing on to deployment:

 * Installation of Docker has already been performed. It's preferable to install Docker CE.
 * Installation of k8s in a single-node or multi-node cluster.

.. _controller_services_cli:

Download Clover CLI
-------------------

Download the cloverctl binary from the location below::

    $ curl -L https://github.com/opnfv/clover/raw/stable/gambia/download/cloverctl.tar.gz | tar xz
    $ cd cloverctl
    $ export PATH=$PWD:$PATH

To begin deploying Clover services, ensure the correct k8s context is enabled. Validate that
the CLI can interact with the k8s API with the command::

    $ cloverctl get services

The command above must return a listing of the current k8s services similar to the output of
'kubectl get svc --all-namespaces'.

.. _controller_services_controller:

Deploying clover-controller
---------------------------

To deploy the **clover-controller** service, use the command below:

.. code-block:: bash

    $ cloverctl create system controller

The k8s pod listing below must include the **clover-controller** pod in the **clover-system**
namespace:

.. code-block:: bash

    $ kubectl get pods --all-namespaces | grep clover-controller

    NAMESPACE      NAME                                    READY      STATUS
    clover-system  clover-controller-74d8596bb5-jczqz      1/1        Running

.. _exposing_clover_controller:

Exposing clover-controller
==========================

To expose the **clover-controller** deployment outside of the k8s cluster, a k8s NodePort
or LoadBalancer service must be employed.

Using NodePort
--------------

To use a NodePort for the **clover-controller** service, use the following command::

    $ cloverctl create system controller nodeport

The NodePort default is to use port 32044. To modify this, edit the yaml relative
to the **cloverctl** path at ``yaml/controller/service_nodeport.yaml`` before invoking
the command above. Delete the ``nodePort:`` key in the yaml to let k8s select an
available port within the the range 30000-32767.

Using LoadBalancer
------------------

For k8s clusters that support a LoadBalancer service, such as GKE, one can be created for
**clover-controller** with the following command::

    $ cloverctl create system controller lb

Setup with cloverctl CLI
------------------------

The **cloverctl** CLI will communicate with **clover-controller** on the service exposed above
and requires the IP address of either the load balancer or a cluster node IP address, if a
NodePort service is used. For a LoadBalancer service, **cloverctl** will automatically find
the IP address to use and no further action is required.

However, if a NodePort service is used, an additional step is required to configure the IP
address for **cloverctl** to target. This may be the CNI (ex. flannel/weave) IP address or the IP
address of an k8s node interface. The **cloverctl** CLI will automatically determine the
NodePort port number configured. To configure the IP address, create a file named
``.cloverctl.yaml`` and add a single line to the yaml file with the following::

    ControllerIP: <IP addresss>

This file must be located in your ``HOME`` directory or in the same directory as the **cloverctl**
binary.

Uninstall from Kubernetes environment
=====================================

Delete with Clover CLI
-----------------------

When you're finished working with Clover system services, you can uninstall it with the
following command:

.. code-block:: bash

     $ cloverctl delete system controller
     $ cloverctl delete system controller nodeport # for NodePort
     $ cloverctl delete system controller lb # for LoadBalancer


The commands above will remove the clover-controller deployment and service resources
created from the current k8s context.

Uninstall from Docker environment
=================================

The OPNFV docker image for the **clover-controller** can be removed with the following commands
from nodes in the k8s cluster.

.. code-block:: bash

    $ docker rmi opnfv/clover-controller
