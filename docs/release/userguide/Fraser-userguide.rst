.. This work is licensed under a Creative Commons Attribution 4.0 International License.
.. http://creativecommons.org/licenses/by/4.0
.. SPDX-License-Identifier CC-BY-4.0
.. (c) optionally add copywriters name


================================================================
Clover User Guide (Fraser Release)
================================================================

This document provides the Clover user guide for OPNFV Fraser release.

.. contents::
   :depth: 3
   :local:


Description
===========

As project Clover's first release, Fraser release includes installation
and simple validation of foundational upstream projects including Istio,
fluentd, Jaeger, and Prometheus. Clover Fraser release also provides a
sample VNF which follows micro-service design pattern, its Kubernetes
manifest, and an automatic scipt to demonstrate a sample A-B testing use
case using the sample VNF running on Istio with trace data exposed to
Jaeger.

What is in Fraser?
==================

 * a sample micro-service composed VNF

 * logging module: fluentd and elasticsearch Kubernetes manifests,
   and fluentd installation validation

 * tracing module: jaeger Kubernetes manifest, installation validation,
   jaegar tracing query tools, module for trace data output to datastore

 * monitoring module: prometheus Kubernetes manifest, installation
   validation, sample Prometheous query of Istio related metrics

 * Istio route-rules sample yaml and validation tools

 * Test scripts

 * Sample code for an A-B testing demo shown during ONS

Usage
=====

 * Python modules to validate installation of fluentd, Jaeger, and
   Prometheus

 * Installation and deployment of a sample VNF
   - VNF designed and implemented with micro-service design pattern
   - tested and validated via Istio service mesh tools

 * sample tool to validate Istio route rules:
   tools/python clover_validate_route_rules.py -s <service name> -t <test id>

 * an example use case: A-B testing:
   test/fraser_a_b_test.py -t yaml/fraser_a_b_test.yaml -p <tracing port num>
   *** detail procedure to run sample A-B testing at docs/configguide/...
