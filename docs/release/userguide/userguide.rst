.. This work is licensed under a Creative Commons Attribution 4.0 International License.
.. http://creativecommons.org/licenses/by/4.0
.. SPDX-License-Identifier CC-BY-4.0
.. (c) Authors of Clover


================================================================
Clover User Guide (Fraser Release)
================================================================

This document provides the Clover user guide for the OPNFV Fraser release.

Description
===========

As project Clover's first release, the Fraser release includes installation and simple
validation of foundational upstream projects including Istio, fluentd, Jaeger, and
Prometheus. The Clover Fraser release also provides a sample set of web-oriented network
services, which follow a micro-service design pattern, its Kubernetes manifest, and an
automated script to demonstrate a sample A-B testing use-case. The A-B sample script
validates performance criteria using Istio request routing functionality leveraging
the sample services deployed within Istio and the tracing data available within Jaeger.

What is in Fraser?
==================

 * Sample micro-service composed VNF named Service Delivery Controller (SDC)

 * Logging module: fluentd and elasticsearch Kubernetes manifests,
   and fluentd installation validation

 * Tracing module: Jaeger Kubernetes manifest, installation validation,
   Jaegar tracing query tools, and module for trace data output to datastore

 * Monitoring module: Prometheus Kubernetes manifest, installation
   validation, and sample Prometheous query of Istio related metrics

 * Istio route-rules sample yaml and validation tools

 * Test scripts

 * Sample code for an A-B testing demo shown during ONS North America 2018

Usage
=====

 * Python modules to validate installation of fluentd logging, Jaeger tracing, and
   Prometheus monitoring. Deployment and validation instructions can be found at:
   :ref:`logging`, :ref:`tracing`, and :ref:`monitoring` respectively.

 * Deployment and usage of SDC sample
   - Services designed and implemented with micro-service design pattern
   - Tested and validated via Istio service mesh tools
   Detailed usage instructions for the sample can be found at :ref:`sdc_config_guide`

 * An example use-case for A-B testing. Detailed usage instructions for this sample A-B
   validation can be found at: :ref:`a_b_config_guide`

 * Sample tool to validate Istio route rules:
   tools/python clover_validate_route_rules.py -s <service name> -t <test id>
