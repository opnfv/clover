.. This work is licensed under a Creative Commons Attribution 4.0 International License.
.. http://creativecommons.org/licenses/by/4.0
.. SPDX-License-Identifier CC-BY-4.0
.. (c) optionally add copywriters name

.. _a_b_config_guide:

=======================
A-B Configuration Guide
=======================

This is a placeholder file for now

- ensure Istio is in the path
- ensure old route rule deleted
- istioctl -n default delete routerules lb-default
- redis port forward
- clover/test/yaml/fraser_a_b_test.yaml
- change ingress port
