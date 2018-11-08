.. This work is licensed under a Creative Commons Attribution 4.0 International License.
.. http://creativecommons.org/licenses/by/4.0
.. SPDX-License-Identifier CC-BY-4.0
.. (c) Authors of Clover

.. _clovisor_config_guide:

============================
Clovisor Configuration Guide
============================

Clovisor requires minimal to no configurations to function as a network tracer.
It expects configurations to be set at a redis sever running at clover-system
namespace.

No Configuration 
================

If redis server isn't running as service name **redis** in namespace
**clover-system** or there isn't any configuration related to Clovisor in that
redis service, then Clovisor would monitor all pods under the **default**
namespace. The traces would be sent to **jaeger-collector** service under the
**clover-system** namespace

Using redis-cli
===============

Install ``redis-cli`` on the client machine, and look up redis IP address:

.. code-block:: bash

    $ kubectl get services -n clover-system

which one may get something like the following:

.. code-block:: bash

    $
    NAME      TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)    AGE
    redis     ClusterIP   10.109.151.40   <none>        6379/TCP   16s

if (like above), the external IP isn't visible, one may be able to get the pod
IP address directly via the pod (for example, it works with Flannel as CNI
plugin):

.. code-block:: bash

    $ kubectl get pods -n clover-system -o=wide
    NAME      READY     STATUS    RESTARTS   AGE       IP             NODE
    redis     2/2       Running   0          34m       10.244.0.187   clover1804

and one can connect to redis via::

    redis-cli -h 10.244.0.187 -p 6379

Jaeger Collector Configuration
==============================

Clovisor allows user to specify the Jaeger service for which Clovisor would send
the network traces to. This is configured via setting the values for
keys **clovisor_jaeger_collector** and **clovisor_jaeger_agent**::

    redis> SET clovisor_jaeger_collector "jaeger-collector.istio-system:14268"
    "OK"
    redis> SET clovisor_jaeger_agent "jaeger-agent.istio-system:6831"
    "OK"

Configure Monitoring Namespace and Labels
=========================================

Configruation Value String Format:
----------------------------------

    <namespace>[:label-key:label-value]

User can configure namespace(s) for Clovisor to tap into via adding namespace
configuration in redis list **clovisor_labels**::

    redis> LPUSH clovisor_labels "my-namespace"
    (integer) 1

the above command will cause Clovisor to **NOT** monitor the pods in **default**
namespace, and only monitor the pods under **my-namespace**.

If user wants to monitor both 'default' and 'my-namespace', she needs to
explicitly add 'default' namespace back to the list::

    redis> LPUSH clovisor_labels "default"
    (integer) 2
    redis> LRANGE clovisor_labels 0 -1
    1.) "default"
    2.) "my-namespace"

Clovisor allows user to optionally specify which label match on pods to further
filter the pods to monitor::

    redis> LPUSH clovisor_labels "my-2nd-ns:app:database"
    (integer) 1

the above configuration would result in Clovisor only monitoring pods in
my-2nd-ns namespace which matches the label "app:database"

User can specify multiple labels to filter via adding more configuration
entries::

    redis> LPUSH clovisor_labels "my-2nd-ns:app:web"
    (integer) 2
    redis> LRANGE clovisor_labels 0 -1
    1.) "my-2nd-ns:app:web"
    2.) "my-2nd-ns:app:database"

the result is that Clovisor would monitor pods under namespace my-2nd-ns which
match **EITHER** app:database **OR** app:web

Currently Clovisor does **NOT** support filtering of more than one label per
filter, i.e., no configuration option to specify a case where a pod in a
namespace needs to be matched with TWO or more labels to be monitored

Configure Egress Match IP address, Port Number, and Matching Pods
=================================================================

Configruation Value String Format:
----------------------------------

    <IP Address>:<TCP Port Number>[:<Pod Name Prefix>]

By default, Clovisor only traces packets that goes to a pod via its service
port, and the response packets, i.e., from pod back to client. User can
configure tracing packet going **OUT** of the pod to the next microservice, or
an external service also via the **clovior_egress_match** list::

    redis> LPUSH clovior_egress_match "10.0.0.1:3456"
    (integer) 1

the command above will cause Clovisor to trace packet going out of ALL pods
under monitoring to match IP address 10.0.0.1 and destination TCP port 3456 on
the **EGRESS** side --- that is, packets going out of the pod.

User can also choose to ignore the outbound IP address, and only specify the
port to trace via setting IP address to zero::

    redis> LPUSH clovior_egress_match "0:3456"
    (integer) 1

the command above will cause Clovisor to trace packets going out of all the pods
under monitoring that match destination TCP port 3456.

User can further specify a specific pod prefix for such egress rule to be
applied::

    redis> LPUSH clovior_egress_match "0:3456:proxy"
    (integer) 1

the command above will cause Clovisor to trace packets going out of pods under
monitoring which have name starting with the string "proxy" that match destination
TCP port 3456
