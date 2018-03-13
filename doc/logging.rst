#######
Logging
#######

************
Installation
************

Currently, we use the `sample configuration`_ in Istio to install fluentd::

    cd clover/logging
    kubectl apply -f install

.. _sample configuration: https://istio.io/docs/tasks/telemetry/fluentd.html

********
Validate
********

The scripts in ``clover/logging`` validates fluentd installation::

    python clover/logging/validate.py
