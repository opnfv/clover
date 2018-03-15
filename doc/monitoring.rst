##########
Monitoring
##########

************
Installation
************

Currently, we use the Istio build-in prometheus addon to install prometheus::

    cd <istio-release-path>
    kubectl apply -f install/kubernetes/addons/prometheus.yaml

********
Validate
********

Setup port-forwarding for prometheus by executing the following command::

    kubectl -n istio-system port-forward $(kubectl -n istio-system get pod -l app=prometheus -o jsonpath='{.items[0].metadata.name}') 9090:9090 &

Run the scripts in ``clover/monitoring`` validates prometheus installation::

    python clover/monitoring/validate.py

It validates the installation with the following criterias

#. [DONE] prometheus pod is in Running state
#. [DONE] prometheus is conneted to monitoring targets
#. [TODO] test collecting telemetry data from istio
#. [TODO] TBD
