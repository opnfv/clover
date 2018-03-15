#######
Tracing
#######

************
Installation
************

Currently, we use the Jaeger tracing all-in-one Kubernetes template for development and testing,
which uses in-memory storage. It can be deployed to the istio-system namespace with the
following command::

    kubectl apply -n istio-system -f https://raw.githubusercontent.com/jaegertracing/jaeger-kubernetes/master/all-in-one/jaeger-all-in-one-template.yml

The standard Jaeger REST port is at 16686. To make this service available outside of the
Kubernetes cluster, use the following command::

    kubectl expose -n istio-system deployment jaeger-deployment --port=16686 --type=NodePort

Kubernetes will expose the Jaeger service on another port, which can be found with::

    kubectl get svc -n istio-system

An example listing from the command above is shown below where the Jaeger service is exposed
externally on port 30888::

    istio-system   jaeger-deployment   NodePort  10.104.113.94  <none> 16686:30888/TCP

Jaeger will be accessible using the host IP of the Kubernetes cluster and port provided.

********
Validate
********

The script in ``clover/tracing`` validates Jaeger installation::

    python clover/tracing/validate.py

It validates the installation with the following criteria:

#. Existence of Jaeger all-in-one deployment using Kubernetes
#. Jaeger service is accessible using IP address and port configured in installation steps
#. Jaeger can retrieve default service listing for default Istio components
#. TBD - consider installation of production setup with cassandra or elastic search
