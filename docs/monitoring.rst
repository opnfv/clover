.. This work is licensed under a Creative Commons Attribution 4.0 International
.. License.
.. http://creativecommons.org/licenses/by/4.0
.. (c) OPNFV, Authors of Clover

.. _monitoring:

##########
Monitoring
##########

************
Installation
************

Currently, we use the Istio built-in Prometheus add-on to install Prometheus::

    cd <istio-release-path>
    kubectl apply -f install/kubernetes/addons/prometheus.yaml


Alternatively, both Prometheus and Jaeger can be installed in combination with the
Clover container using the command::

    $ sudo docker run --rm \
    -v ~/.kube/config:/root/.kube/config \
    opnfv/clover \
    /bin/bash -c '/home/opnfv/repos/clover/samples/scenarios/view.sh'

********
Validate
********

Setup port-forwarding for Prometheus by executing the following command::

    kubectl -n istio-system port-forward $(kubectl -n istio-system get pod -l app=prometheus -o jsonpath='{.items[0].metadata.name}') 9090:9090 &

Run the scripts in ``clover/monitoring`` to validate the Prometheus installation::

    python clover/monitoring/validate.py

It validates the installation with the following criteria:

#. Prometheus pod is in running state
#. Prometheus is connected to monitoring targets
