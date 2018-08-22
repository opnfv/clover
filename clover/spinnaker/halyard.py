#!/bin/python

import lib.halyard_base as base
import time
from clover.orchestration.kube_client import KubeClient

namespace = 'spinnaker'
client = KubeClient()

def list_accounts(provider):
    account_list = base.list_accounts(provider)
    return account_list

def delete_account(provider, accountname):
    result = base.delete_account(provider, accountname)
    if result != "SUCCEEDED":
        print "Delete account failed"
        return result

    apply_result = base.apply_deploy()
    if apply_result == "SUCCEEDED":
        print "Delete account successfully"
    else:
        print "Delete account failed"

    return apply_result

def add_k8s_account(accountname, kubeconfigfile,
                providerversion=None, registries=[]):
    # Note: if providerversion is V1, must provider registries.
    if base.is_account_exist("kubernetes",accountname):
        return "FAILED"
    if providerversion == None or providerversion == 'V1':
        providerversion = None
        if 0 == len(registries) or isinstance(registries, list) == False:
            print "please provider docker registries or the type of registries is not list"
            return "FAILED"
    # Copy kubectl file to halyard pod
    hal_kubeconfigfile = "/home/spinnaker/config" + \
                 time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime())
    spinnaker_pods = client.find_pod_by_namespace(namespace)
    for pod in spinnaker_pods:
        if pod.find("spin-halyard") == 0:
            client.copy_file_to_pod(kubeconfigfile,
                                         hal_kubeconfigfile,
                                         pod, namespace)
    dockerRegistries = []
    for registry in registries:
        if not base.is_account_exist("dockerRegistry",registry):
            print ("Please add docker registry: %s" %registry)
            return "FAILED"
        docker_dict = {"accountName":registry, "namespaces":[]}
        dockerRegistries.append(docker_dict)

    data = {
            "name": accountname,
            "requiredGroupMembership": [],
            "providerVersion": providerversion,
            "permissions": {},
            "dockerRegistries": dockerRegistries,
            "context": None,
            "cluster": None,
            "user": None,
            "configureImagePullSecrets": "true",
            "serviceAccount": None,
            "cacheThreads": 1,
            "namespaces": [],
            "omitNamespaces": [],
            "kinds": [],
            "omitKinds": [],
            "customResources": [],
            "cachingPolicies": [],
            "kubeconfigFile": hal_kubeconfigfile,
            "kubeconfigContents": None,
            "kubectlPath": None,
            "namingStrategy": None,
            "skin": None,
            "debug": None,
            "oauthScopes": [],
            "oauthServiceAccount": None,
            "oAuthServiceAccount": None,
            "oAuthScopes": []
          }
#    print data
    result = base.add_account("kubernetes",data)
    return result

def add_docker_account(address, accountname, repositories=[],
                       username=None, password=None, validate='true'):

    if base.is_account_exist("dockerRegistry",accountname):
        return "FAILED"

    data = {
            "name": accountname,
            "requiredGroupMembership": [],
            "providerVersion": None,
            "permissions": {},
            "address": address,
            "username": username,
            "password": password,
            "email": "fake.email@spinnaker.io",
            "cacheIntervalSeconds": 30,
            "clientTimeoutMillis": 60000,
            "cacheThreads": 1,
            "paginateSize": 100,
            "sortTagsByDate": False,
            "trackDigests": False,
            "insecureRegistry": False,
            "repositories": repositories,
            "passwordFile": None,
            "dockerconfigFile": None
          }
    result = base.add_account("dockerRegistry",data)
    if result == "SUCCEEDED":
        print "Add account successfully"
    else:
        print "Add account failed"
    return result

