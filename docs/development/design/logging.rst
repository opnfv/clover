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

It validates the installation with the following criterias

#. existence of fluented pod
#. fluentd input is configured correctly
#. TBD

**************************
Understanding how it works
**************************

In clover stack, Istio is configured to automatically gather logs for services
in a mesh. More specificly, it is configured in `Mixer`_::

- when to log
- what to log
- where to log

.. _Mixer: https://istio.io/docs/concepts/policy-and-control/mixer.html

When to log
===========

Istio defines when to log by creating a custom resource ``rule``. For example:

.. code-block:: yaml

    apiVersion: "config.istio.io/v1alpha2"
    kind: rule
    metadata:
    name: newlogtofluentd
    namespace: istio-system
    spec:
    match: "true" # match for all requests
    actions:
    - handler: handler.fluentd
      instances:
      - newlog.logentry

This rule specifies that all instances of ``newlog.logentry`` that matches the
expression will be handled by the specified handler ``handler.fluentd``. We
shall explain ``instances`` and ``handler`` later. The expression ``true`` means
whenever a request arrive at Mixer, it will trigger the actions defined belows.

``rule`` is a custom resource definition from `Istio installation`_.

.. code-block:: yaml

    # Rule to send logentry instances to the fluentd handler
    kind: CustomResourceDefinition
    apiVersion: apiextensions.k8s.io/v1beta1
    metadata:
      name: rules.config.istio.io
      labels:
        package: istio.io.mixer
        istio: core
    spec:
      group: config.istio.io
      names:
        kind: rule
        plural: rules
        singular: rule
    scope: Namespaced
    version: v1alpha2

.. _Istio installation: https://github.com/istio/istio/blob/master/install/kubernetes/templates/istio-mixer.yaml.tmpl

What to log
===========

The instance defines what content to be logged.

> A (request) instance is the result of applying request attributes to the
> template mapping. The mapping is specified as an instance configuration.

For example:

.. code-block:: yaml

    # Configuration for logentry instances
    apiVersion: "config.istio.io/v1alpha2"
    kind: logentry
    metadata:
      name: newlog
      namespace: istio-system
    spec:
      severity: '"info"'
      timestamp: request.time
      variables:
        source: source.labels["app"] | source.service | "unknown"
        user: source.user | "unknown"
        destination: destination.labels["app"] | destination.service | "unknown"
        responseCode: response.code | 0
        responseSize: response.size | 0
        latency: response.duration | "0ms"
      monitored_resource_type: '"UNSPECIFIED"'

The keys under ``spec`` should conform to the template. To learn what fields
are available and valid type, you may need to reference the corresponding
template, in this case, `Log Entry template`_.

The values of each field could be either `Istio attributes`_ or an expression.

> A given Istio deployment has a fixed vocabulary of attributes that it
> understands. The specific vocabulary is determined by the set of attribute
> producers being used in the deployment. The primary attribute producer in
> Istio is Envoy, although Mixer and services can also introduce attributes.

Refer to the `Attribute Vocabulary`_ to learn the full set.

By the way, ``logentry`` is also a custom resource definition created by Istio.

.. _Istio attributes: https://istio.io/docs/concepts/policy-and-control/attributes.html
.. _Attribute Vocabulary: https://istio.io/docs/reference/config/mixer/attribute-vocabulary.html
.. _Log Entry template: https://istio.io/docs/reference/config/template/logentry.html

Where to log
============

For log, the handler defines where these information will be handled, in this
example, a fluentd daemon on fluentd-es.logging:24224.

.. code-block:: yaml

    # Configuration for a fluentd handler
    apiVersion: "config.istio.io/v1alpha2"
    kind: fluentd
    metadata:
      name: handler
      namespace: istio-system
    spec:
      address: "fluentd-es.logging:24224"

In this example, handlers (``handler.fluentd``) configure `Adapters`_
(``fluentd``) to handle the data delivered from the created instances
(``newlog.logentry``).

An adapter only accepts instance of specified kind. For example,
`fluentd adapter`_ accepts logentry but not other kinds.

.. _Adapters: https://istio.io/docs/concepts/policy-and-control/mixer.html#adapters
.. _fluentd adapter: https://istio.io/docs/reference/config/adapters/fluentd.html
