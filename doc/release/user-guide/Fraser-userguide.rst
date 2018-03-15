.. This work is licensed under a Creative Commons Attribution 4.0 International License.
.. http://creativecommons.org/licenses/by/4.0
.. SPDX-License-Identifier CC-BY-4.0
.. (c) optionally add copywriters name


================================================================
Clover User Guide (Fraser Release)
================================================================

This document provides the user guide for Fraser release of Clover.

.. contents::
   :depth: 3
   :local:


Description
===========

Project Clover was established to investigate best practice to implement,
build, deploy, and operate virtual network functions as cloud native
applications. "Cloud native" has a ever evolving and expanding definition,
and in Clover, the focus is effectively running and operating VNFs built
in a micro-service design pattern running on Docker containers and
orchestrated by Kubernetes.

The strength of cloud native applications is their operablity and
scalability. Essential to achieve these qualities is the use of service
mesh. As such, in Fraser release, Clover's emphasis is on demonstrating
running a sample micro-service composed VNF on Istio, the service mesh
platform of Clover's choice in Fraser, and how to maximize visibility
of this sample running in a service mesh.

What is in Fraser?
==================

 * a sample micro-service composed VNF

 * opinionated installation script for Istio 0.6 without CA or
   automatic sidecar injection

 * logging module: fluentd and elasticsearch Kubernetes manifests,
   installation validation, log data correlation in datastore

 * tracing module: jaeger Kubernetes manifest, installation validation,
   jaegar tracing query tools, trace data correlation in datastore

 * monitoring module: prometheus Kubernetes manifest, installation
   validation, prometheous query tools for Istio related metrics,
   metrics correlation in datastore

 * Istio route-rules and circuit breaking sample yaml and validation
   tools

 * Test scripts

Usage
=====

 * each modules (service mesh, logging, tracing, monitoring) are Python
   modules with their own set of library calls exposed. The descriptions
   of these library calls are under doc/developer (TBD)

 * tools directory contains Python tools for generic use
   python clover_validate_route_rules.py -s <service name> -n <number of tests>
   [more TBD]

 * an example scenario:
   version 2 (v2) of a micro-service component is deployed
   Istio route rule is applied to send only 20% traffic to v2
   Clover tool validates traffic conformance with route rules
   user specify via yaml the "success" expectation of v2 (latency,
   performance, session loss...etc)
   Clover tool validates sessions conformance with user defined expectations
   An action is invoked to move 100% traffic to v2
   Clover tool validates traffic conformance with route rules
