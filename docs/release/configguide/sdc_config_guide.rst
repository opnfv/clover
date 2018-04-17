.. This work is licensed under a Creative Commons Attribution 4.0 International License.
.. http://creativecommons.org/licenses/by/4.0
.. SPDX-License-Identifier CC-BY-4.0
.. (c) optionally add copywriters name


=======================================
Clover SDC Sample Configuration Guide
=======================================

This document provides a guide to use the SDC sample, which is initially delivered in the Clover
Fraser release.

.. contents::
   :depth: 3
   :local:


Overview
=========

The Service Delivery Controller (SDC) is a sample application that allows the flow of ingress
HTTP traffic to be controlled and inspected in an Istio service mesh. It provides the ability
to demonstrate the Istio sandbox including a service mesh and surrounding tools including
tracing, monitoring, and logging.

The SDC sample comprises the following micro-services:

 * Proxy

 * Load Balancer

 * Intrusion Detection System

 * Server

< TBA insert table here with number of elements, deployment name, purpose, etc.>

Additionally, the sample uses other ancillary elements including:

 * A Redis in-memory data store for the snort IDS service to write alerts. It can also be used
   by the Clover tracing module to analyze traces over time.

 * A Kubernetes Ingress resource to manage external access to the service mesh.

.. image:: imgs/sdc_sample.png
    :align: center
    :scale: 100%

< TBA explain traffic flow>

Deploying the sample app
========================

Prerequisites
-------------

The following assumptions must be met before continuing on to deployment:

 * Installation of Kubernetes has already been performed. The installation in this guide was
   executed in a single-node Kubernetes cluster.
 * Installation of a pod network that supports the Container Network Interface (CNI). It is
   recommended to use flannel, as most development work employed this network add-on.
 * Installation of Istio and Istio client (istioctl) is in your PATH (for deploy from source)

Deploy with Clover container
----------------------------

The easiest way to deploy the sample is to use the Clover container by pulling the
container and executing a top-level deploy script using the following two commands:

.. code-block:: bash

    $ docker pull opnfv/clover:<release_tag>

The <release_tag> should be **6.0.0** for the Fraser release. However, the latest
will be pulled if the tag is unspecified.

.. code-block:: bash

    $ sudo docker run --rm \
    -v ~/.kube/config:/root/.kube/config \
    opnfv/clover \
    /bin/bash -c '/home/opnfv/repos/clover/samples/scenarios/deploy.sh'

The deploy script invoked above begins by installing Istio 0.6.0 into your Kubernetes environment. It
proceeds to deploy the entire SDC manifest. If you've chosen to employ this method of deployment,
you may skip the next section.

Deploy from source
------------------

Ensure Istio 0.6.0 is installed, as a prerequisite, using the following commands:

.. code-block:: bash

    $ curl -L https://github.com/istio/istio/releases/download/0.6.0/istio-0.6.0-linux.tar.gz | tar xz
    $ cd istio-0.6.0
    $ export PATH=$PWD/bin:$PATH
    $ kubectl apply -f install/kubernetes/istio.yaml

The above sequence of commands installs Istio with manual sidecar injection without mutual TLS
authentication between sidecars.

To continue to deploy from the source code, clone the Clover git repository and navigate to
within the samples directory as shown below:

.. code-block:: bash

    $ git clone https://gerrit.opnfv.org/gerrit/clover
    $ cd clover/samples/scenarios

To deploy the sample in the default Kubernetes namespace, use the following command for Istio
manual sidecar injection:

.. code-block:: bash

    $ kubectl apply -f <(istioctl kube-inject --debug -f service_delivery_controller_opnfv.yaml)

To deploy in another namespace, use the '-n' option. An example namespace of 'sdc' is shown below:

.. code-block:: bash

    $ kubectl create namespace sdc
    $ kubectl apply -n sdc -f <(istioctl kube-inject --debug -f service_delivery_controller_opnfv.yaml)

When using the above SDC  manifest, all required docker images will automatically be pulled
from the OPNFV public Dockerhub registry. An example of using a Docker local registry is also
provided in the ``/clover/samples/scenario`` directory.

Verifying the deployment
------------------------

To verify the entire SDC sample is deployed, ensure the following pods have been deployed:

.. code-block:: bash

    $ kubectl get pod --all-namespaces

SDC pods must include the following listing:

.. code-block:: bash

    $ NAMESPACE      NAME                                    READY     STATUS
    default        clover-server1-68c4755d9c-7s5q8           2/2       Running
    default        clover-server2-57d8b786-rf5x7             2/2       Running
    default        clover-server3-556d5f79cf-hk6rv           2/2       Running
    default        clover-server4-6d9469b884-8srbk           2/2       Running
    default        clover-server5-5d64f74bf-l7wqc            2/2       Running
    default        http-lb-v1-59946c5744-w658d               2/2       Running
    default        http-lb-v2-5df78b6849-splp9               2/2       Running
    default        proxy-access-control-6b564b95d9-jg5wm     2/2       Running
    default        redis                                     2/2       Running
    default        snort-ids-5cc97fc6f-zhh5l                 2/2       Running

Istio pods must include the following listing:

.. code-block:: bash

    $ NAMESPACE    NAME                               READY     STATUS
    istio-system   istio-ca-59f6dcb7d9-9frgt          1/1       Running
    istio-system   istio-ingress-779649ff5b-mcpgr     1/1       Running
    istio-system   istio-mixer-7f4fd7dff-mjpr8        3/3       Running
    istio-system   istio-pilot-5f5f76ddc8-cglxs       2/2       Running

Determining the ingress IP and port
-----------------------------------

To determine how incoming http traffic on port 80 will be translated, use the following command:

.. code-block:: bash

    $ kubectl get svc -n istio-system
    NAME                TYPE           CLUSTER-IP       EXTERNAL-IP   PORT(S)
    istio-ingress       LoadBalancer   10.104.208.165   <pending>     80:32410/TCP,443:31045/TCP

**Note, the CLUSTER-IP of the service will be unused in this example since load balancing service
types are unsupported in this configuration. It is normal for the EXTERNAL-IP to show status
<pending> indefinitely**

In this example, traffic arriving on port 32410 will flow to istio-ingress. The
istio-ingress service will route traffic to the proxy-access-control service based on a
configured ingress rule, which defines a gateway for external traffic to enter
the Istio service mesh. This makes the traffic management and policy features of Istio available
for edge services.

Using the sample app
====================

To confirm the scenario is running properly, HTTP GET requests can be made from an external 
host with a destination of the Kubernetes cluster. Requests can be invoked from the host OS
of the Kubernetes cluster. Modify the port used below (32410) with the port obtained from
the previous section. If flannel is being used, requests can use the default flannel
CNI IP address, as shown below:

.. code-block:: bash

    $ wget http://10.244.0.1:32410/
    $ curl http://10.244.0.1:32410/

An HTTP response will be returned as a result of the wget or curl command, if the SDC sample
is operating correctly. However, the visibility into what micro-services were accessed within
the service mesh remains hidden. The next section shows how to see the internals of the Istio
service mesh.

Exposing tracing and monitoring
-------------------------------

To gain insight into the service mesh, the Jaeger tracing and Prometheus monitoring tools
can also be deployed. These tools can show how the sample functions in the service mesh.
Using the Clover container, issue the following command to deploy these tools
into your Kubernetes environment:

.. code-block:: bash

    $ sudo docker run --rm \
    -v ~/.kube/config:/root/.kube/config \
    opnfv/clover \
    /bin/bash -c '/home/opnfv/repos/clover/samples/scenarios/view.sh'

The Jaeger tracing UI is exposed outside of the Kubernetes cluster via any node IP in the cluster
using the following commands **(above command already executes the two commands below)**:

.. code-block:: bash

    $ kubectl expose -n istio-system deployment jaeger-deployment --port=16686 --type=NodePort

Likewise, the Promethues monitoring UI is exposed with the following command:

.. code-block:: bash

    $ kubectl expose -n istio-system deployment prometheus --port=9090 --type=NodePort

To find the ports the Jaeger tracing and Prometheus monitoring UIs are exposed on, use the
following command:

.. code-block:: bash

    $ kubectl get svc --all-namespaces
    NAMESPACE      NAME              TYPE      CLUSTER-IP   EXTERNAL-IP   PORT(S)
    istio-system   jaeger-deployment NodePort  10.105.94.85 <none>        16686:32174/TCP
    istio-system   prometheus        NodePort  10.97.74.230 <none>        9090:32708/TCP

In the example above, the Jaeger tracing web-based UI will be available on port 32171 and
the Prometheus monitoring UI on port 32708. In your browser, navigate to the following
URLs for Jaeger and Prometheus respectively::

    http://<node IP>:32174
    http://<node IP>:32708

Where node IP is an IP from one of the Kubernetes cluster node(s) (from host OS).

Modifying the run-time configuration of micro-services
======================================================

The following control-plane actions can be invoked via GRPC messaging from a controlling agent.
For this example, it is conducted from the host OS of a Kubernetes cluster node.

**Note, the preceding instructions assume the flannel network CNI plugin is installed. Other
Kubernetes networking plugins may work but have not been validated.**

Modifying the http-lb server list
----------------------------------

By default, both versions of the load balancers send incoming HTTP requests to clover-server1/2/3
in round-robin fashion. To have the version 2 load balancer (http-lb-v2) send its traffic to
clover-server4/5 instead, issue the following command:

.. code-block:: bash

    $ sudo docker run --rm \
    -v ~/.kube/config:/root/.kube/config \
    opnfv/clover \
    /bin/bash -c 'python /home/opnfv/repos/clover/samples/services/nginx/docker/grpc/nginx_client.py \
    --service_type=lbv2 --service_name=http-lb-v2'

Adding rules to snort-ids
--------------------------

The snort service installs the readily available community rules. An initial, basic provision to
allow custom rule additions has been implemented within this release. A custom rule will trigger
alerts and can be defined in order to inspect network traffic. This capability, including
rule manipulation, will be further expounded upon in subsequent releases. For the time being, the
following basic rule additions can be performed using a client sample script.

A snort IDS alert can be triggered by adding the HTTP User-Agent string shown below. The
signature that invokes this alert is part of the community rules that are installed in the
snort service by default. Using the curl or wget commands below, an alert can be observed using
the Jaeger tracing browser UI. It will be displayed as a GRPC message on port 50054 from the
**snort-ids** service to the **proxy-access-control** service.

.. code-block:: bash

    $ wget -U 'asafaweb.com' http://10.244.0.1:32410/

Or alternatively with curl, issue this command to trigger the alert:

.. code-block:: bash

    $ curl -A 'asafaweb.com' http://10.244.0.1:32410/

The community rule can be copied to local rules in order to ensure an alert is generated
each time the HTTP GET request is observed by snort using the following command.

.. code-block:: bash

    $ sudo docker run --rm \
    -v ~/.kube/config:/root/.kube/config \
    opnfv/clover \
    /bin/bash -c 'python /home/opnfv/repos/clover/samples/services/snort_ids/docker/grpc/snort_client.py \
    --cmd=addscan --service_name=snort-ids'

To add an ICMP rule to snort service, use the following command:

.. code-block:: bash

    $ sudo docker run --rm \
    -v ~/.kube/config:/root/.kube/config \
    opnfv/clover \
    /bin/bash -c 'python /home/opnfv/repos/clover/samples/services/snort_ids/docker/grpc/snort_client.py \
    --cmd=addicmp --service_name=snort-ids'

The above command will trigger alerts whenever ICMP packets are observed by the snort service.
An alert can be generated by pinging the snort service using the flannel IP address assigned to
the **snort-ids** pod.

Uninstall from Kubernetes envionment
====================================

Delete with Clover container
----------------------------

When your finished working on the SDC sample, you can uninstall it with the
following command:

.. code-block:: bash

     $ sudo docker run --rm \
    -v ~/.kube/config:/root/.kube/config \
    opnfv/clover \
    /bin/bash -c '/home/opnfv/repos/clover/samples/scenarios/clean.sh'

The command above will remove the SDC sample services, Istio components and Jaeger/Prometheus
tools from your Kubernetes environment.

Delete from source
------------------

The SDC sample services can be uninstalled from the source code using the commands below:

.. code-block:: bash

    $ cd clover/samples/scenarios
    $ kubectl delete -f service_delivery_controller_opnfv.yaml

    pod "redis" deleted
    service "redis" deleted
    deployment "clover-server1" deleted
    service "clover-server1" deleted
    deployment "clover-server2" deleted
    service "clover-server2" deleted
    deployment "clover-server3" deleted
    service "clover-server3" deleted
    deployment "clover-server4" deleted
    service "clover-server4" deleted
    deployment "clover-server5" deleted
    service "clover-server5" deleted
    deployment "http-lb-v1" deleted
    deployment "http-lb-v2" deleted
    service "http-lb" deleted
    deployment "snort-ids" deleted
    service "snort-ids" deleted
    deployment "proxy-access-control" deleted
    service "proxy-access-control" deleted
    ingress "proxy-gateway" deleted

Uninstall from Docker environment
=================================

The OPNFV docker images can be removed with the following commands:

.. code-block:: bash

    $ docker rmi opnfv/clover-ns-nginx-proxy
    $ docker rmi opnfv/clover-ns-nginx-lb
    $ docker rmi opnfv/clover-ns-nginx-server
    $ docker rmi opnfv/clover-ns-snort-ids
    $ docker rmi opnfv/clover

The Redis, Prometheus and Jaeger docker images can be removed with the following commands:

.. code-block:: bash

    $ docker rmi k8s.gcr.io/redis
    $ docker rmi kubernetes/redis
    $ docker rmi prom/prometheus
    $ docker rmi jaegertracing/all-in-one

If docker images were built locally, they can be removed with the following commands:

.. code-block:: bash

    $ docker rmi localhost:5000/clover-ns-nginx-proxy
    $ docker rmi clover-ns-nginx-proxy
    $ docker rmi localhost:5000/clover-ns-nginx-lb
    $ docker rmi clover-ns-nginx-lb
    $ docker rmi localhost:5000/clover-ns-nginx-server
    $ docker rmi clover-ns-nginx-server
    $ docker rmi localhost:5000/clover-ns-snort-ids
    $ docker rmi clover-ns-snort-ids
