########
Clovisor
########

*****************
What is Clovisor?
*****************

One of Clover's goals is to investigate an optimal way to perform network
tracing in cloud native environment. Clovisor is project Clover's initial
attempt to provide such solution.

Clovisor is named due to it being "Clover's use of IOVisor". `IOVisor`_ is a
set of tools to ease eBPF code development for tracing, monitoring, and other
networking functions. BPF stands for Berkeley Packet Filter, an in-kernel
virtual machine like construct which allows developers to inject bytecodes in
various kernel event points. More information regarding BPF can be found
`here`_. Clovisor utilizes the `goBPF`_ module from IOVisor as part of its
control plane, and primarily uses BPF code to perform packet filtering in the
data plane.

.. _IOVisor: https://github.com/iovisor
.. _here: https://cilium.readthedocs.io/en/v1.2/bpf/
.. _goBPF: https://github.com/iovisor/gobpf

**********************
Clovisor Functionality
**********************

Clovisor is primarily a session based network tracing module, that is, it
generates network traces on a per-session basis, i.e., on a request and response
pair basis. It records information pertaining to L3/L4 and L7 (just HTTP 1.0 and
1.1 for now) regarding the session. The traces are sent to Jaeger server who
acts as tracer, or trace collector.

********************
Clovisor Requirement
********************

Clovisor is tested on kernel versions 4.14.x and 4.15.x. For Ubuntu servers
built-in kernel, it requires Ubuntu version 18.04.

*****************
Clovisor Workflow
*****************

Clovisor runs as a `DaemonSet`_ --- that is, it runs on every nodes in a
Kubernetes cluster, including being automatically launched in newly joined node.
Clovior runs in the "clovisor" Kubernetes namespace, and it needs to run in
privilege mode and be granted at least pod and service readable right for the
Kubernetes namespace(s) in which it is monitoring, i.e., a RBAC needs to be set
up to grant such access right to the clovisor namespace service account.

Clovisor looks for its configuration(s) from redis server in clover-system
namespace. The three config info for Clovisor for now are:

#. clovisor_labels, a list of labels which Clovisor would filter for monitoring
#. clovisor_egress_match, a list of interested egress side IP/port for outbound
   traffic monitoring
#. clovisor_jaeger_server, specifying the Jaeger server name / port to send
   traces to

By default Clovisor would monitor all the pods under the 'default' namespace.
It will read the service port name associated with the pod under monitoring,
and use the service port name to determine the network protocol to trace.
Clovisor expects the same service port naming convention / nomenclature as
Istio, which is specified in `istio`_. Clovisor extracts expected network
protocol from these names; some examples are

.. code-block:: yaml

    apiVersion: v1
    kind: Service
    [snip]
    spec:
      ports:
      - port: 1234
        name: http

With the above example in the service specification, Clovisor would specifically
look to trace HTTP packets for packets matching that destination port number on
the pods associated with this service, and filter everything else. The
following has the exact same bahavior

.. code-block:: yaml

    apiVersion: v1
    kind: Service
    [snip]
    spec:
      ports:
      - port: 1234
        name: http-1234

Clovisor derived what TCP port to monitor via the container port exposed by the
pod in pod spec. In the following example:

.. code-block:: yaml

    spec:
      containers:
      - name: foo
        image: localhost:5000/foo
        ports:
        - containerPort: 3456

Packets with destination TCP port number 3456 will be traced for the pod on the
ingress side, likewise for packet with source TCP port number 3456 on the
ingress side (for receiving response traffic tracing). This request-response
pair is sent as a `span`_.

In addition, Clovisor provides egress match configurion where user can
configure the (optional) IP address of the egress side traffic and TCP port
number for EGRESS or outbound side packet tracing. This is particularly useful
for the use case where the pod sends traffic to an external entity (for
example, sending to an external web site on port 80). User can further specify
which pod prefix should the rules be applied.

Clovisor is a session-based network tracer, therefore it would trace both the
request and response packet flow, and extract any information necessary (the
entire packet from IP header up is copied to user space). In Gambia release
Clovisor control plane extracts source/destination IP addresses (from request
packet flow perspective), source/destination TCP port number, and HTTP request
method/URL/protocol as well as response status/status code/protocol, and
overall session duration. These information is being logged via OpenTracing
APIs to Jaeger.

.. _DaemonSet: https://kubernetes.io/docs/concepts/workloads/controllers/daemonset/
.. _istio: https://istio.io/docs/setup/kubernetes/spec-requirements/
.. _span: https://github.com/opentracing/specification/blob/master/specification.md

**********************
Clovisor Control Plane
**********************

There are two main elements of Clovisor control plane: Kubernetes client and
BPF control plane using IOVisor BCC.

Kubernetes client is used for the following needs:

#. fetches the pods pertaining to filter ('default' namespace by default
   without filter)
#. fetches corresponding service port name to determine network protocol to
   trace (TCP by default)
#. extracts veth interface index for pod network interface
#. watches for pod status change, or if new pod got launched that matches the
   filter

Clovisor uses goBPF from IOVisor BCC project to build its control plane for BPF
datapath, which does:

#. via `netlink`_, under the pod veth interface on the Linux host side, creates
   a `QDisc`_ with name 'classact' with ingress and egress filters created
   under it
#. dynamically compiles and loads BPF code "session_tracing.c" and sets ingress
   and egress functions on the filters created above
#. sets up perfMap (shared packet buffer between user space and kernel) and
   sets up kernel channel to poll map write event
#. sets up timer task to periodically logs and traces interested packets

.. _netlink: https://github.com/vishvananda/netlink
.. _QDisc: http://tldp.org/HOWTO/Traffic-Control-HOWTO/components.html

*******************
Clovisor Data Plane
*******************

Clovisor utilizes BPF for data plane packet analysis in kernel. BPF bytecode
runs in kernel and is executed as an event handler. Clovisor's BPF program has
an ingress and egress packet handling functions as loadable modules for
respective event trigger points, i.e., ingress and egress on a particular Linux
network interface, which for Clovisor is the pod associated veth. There are
three tables used by the Clovisor BPF program:

#. dports2proto: control plane -> data plane: the container/service port and
   corresponding protocol (TCP, HTTP...etc) to trace on the ingress side
#. egress_lookup_table: control plane -> data plane: the list of egress IP
   address / ports which Clovisor should trace on the egress side
#. sessions: data plane -> control plane: BPF creates entries to this table to
   record TCP sessions

*****************
Clovisor Clean Up
*****************

As mentioned above, on a per pod basis, Clovisor creates a qdisc called
'classact' per each pod veth interface. This kernel object does not get deleted
by simply killing the Clovisor pod. The cleanup is done via Clovisor either via
pod removal, or when the Clovisor pod is deleted. However, IF the qdisc is not
cleaned up, Clovisor would not be able to tap into that same pod, more
specifically, that pod veth interface. The qdisc can be examined via the
following command::

    sudo tc qdisc show

and you should see something like this::

    qdisc clsact ffff: dev veth4c47cc75 parent ffff:fff1

in case it wasn't removed at the end, user can manually remove it via::

    sudo tc qdisc del dev veth4c47cc75 clsact

(of course, the qdisc should be removed by Clovisor, otherwise it is a Clovisor
bug)
