.. This work is licensed under a Creative Commons Attribution 4.0 International License.
.. http://creativecommons.org/licenses/by/4.0
.. SPDX-License-Identifier CC-BY-4.0
.. (c) Authors of Clover


================================================================
Clover User Guide (Gambia Release)
================================================================

This document provides the Clover user guide for the OPNFV Hunter release.

Description
===========

Clover Hunter builds on previous release to further enhance the toolset for
cloud native network functions operations. The main emphasis on the release are:

#. ONAP SDC on Istio with Clover providing visibility
#. Clovisor enhancement and stability

What is in Hunter?
==================

 * Sample micro-service composed VNF named Service Delivery Controller (SDC)

 * Istio 1.0 support

 * clover-collector: gathers and collects metrics and traces from Prometheus and
   Jaeger, and provides a single access point for such data

 * Visibility: utilizes an analytic engine to correlate and organize data
   collected by clover-collector

 * cloverctl: Clover's new CLI

 * Clovisor: Clover's cloud native, CNI-plugin agnostic network tracing tool

 * Integration of HTTP Security Modules with Istio 1.0

 * JMeter: integrating jmeter as test client

 * Clover UI: sample UI to offer single pane view / configuration point of the
   Clover system

Usage
=====

 * Please refer to configguildes for usage detail on various modules
