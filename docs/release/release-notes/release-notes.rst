.. This work is licensed under a Creative Commons Attribution 4.0 International License.
.. http://creativecommons.org/licenses/by/4.0
.. SPDX-License-Identifier CC-BY-4.0
.. (c) Authors of Clover


This document provides Clover project's release notes for the OPNFV Gambia release.

.. contents::
   :depth: 3
   :local:


Version history
---------------

+--------------------+--------------------+--------------------+--------------------+
| **Date**           | **Ver.**           | **Author**         | **Comment**        |
|                    |                    |                    |                    |
+--------------------+--------------------+--------------------+--------------------+
| 2018-03-14         | Gambia 1.0         | Stephen Wong       | First draft        |
|                    |                    |                    |                    |
+--------------------+--------------------+--------------------+--------------------+

Important notes
===============

The Clover project for OPNFV Gambia is tested on Kubernetes version 1.9 and
1.11. It is only tested on Istio 1.0.

Summary
=======

Clover Gambia release further enhances the Fraser release by providing various
tools to help operators deploy cloud native network functions. These tools
include

#. Collector: gathers and collects metrics and traces from Prometheus and
   Jaeger, respectively, and provides a single access point for such data
#. Visibility: utilizes an analytic engine to correlate and organize data
   gathered by the collector
#. CLI: comprehensive Clover CLI called cloverctl, offering a single management
   tool for operating Clover toolset
#. Network Tracing: CNI plugin agnostic network tracing tool
#. Extended HTTP Security: integrate modsecurity (Web Application Firewall) and
   Snort with Istio gateway via Istio newly added mechanisms to redirect and
   mirror traffic to the network functions
#. HTTP Test Client: bundle JMeter as test client for testing
#. UI: developmental / sample UI to offer single pane view of Clover system
#. Spinnaker Integration: provides automated / programmable cloud provider
   add/update/delete; sample pipeline and installation scripts

Release Data
============

+--------------------------------------+--------------------------------------+
| **Project**                          | Clover                               |
|                                      |                                      |
+--------------------------------------+--------------------------------------+
| **Repo/commit-ID**                   |                                      |
|                                      |                                      |
+--------------------------------------+--------------------------------------+
| **Release designation**              | Gambia                               |
|                                      |                                      |
+--------------------------------------+--------------------------------------+
| **Release date**                     | 2018-11-09
|                                      |                                      |
+--------------------------------------+--------------------------------------+
| **Purpose of the delivery**          | OPNFV Gambia release                 |
|                                      |                                      |
+--------------------------------------+--------------------------------------+

Version change
^^^^^^^^^^^^^^^^

Module version changes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Clover Gambia release will no longer support Istio 0.6, the version of Istio
supported by Clover Gambia release

Document version changes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Clover Gambia has updated the config guide and user guide accordingly, including
new documents for the new features

Reason for version
^^^^^^^^^^^^^^^^^^^^

Feature additions
~~~~~~~~~~~~~~~~~~~~~~~
See Summary above

Bug corrections
~~~~~~~~~~~~~~~~~~~~~
<None>

Known Limitations, Issues and Workarounds
=========================================

System Limitations
^^^^^^^^^^^^^^^^^^^^
TBD

Known issues
^^^^^^^^^^^^^^^
TBD

Workarounds
^^^^^^^^^^^^^^^^^

Test Result
===========


References
==========
