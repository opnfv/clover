# Copyright (c) Authors of Clover
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0

from flask import Blueprint, request, Response
import logging
import lib.halyard_base as base

halyard = Blueprint('halyard', __name__)

@halyard.route("/halyard/addkube", methods=['GET', 'POST'])
def addkubernetes():
    try:
        p = request.json
        accountname = p['Name']
        providerversion = p['ProviderVersion']
        Registries = p['DockerRegistries']
        kubeconfigFile = p['KubeconfigFile']

    except (KeyError, ValueError) as e:
        logging.debug(e)
        return Response('Invalid value in kubernetes yaml', status=400)

    try:
        if base.is_account_exist("kubernetes",accountname):
            return Response("account name has already exist", status=400)
        if providerversion == None or providerversion == 'V1':
            providerversion = None
            if 0 == len(Registries) or isinstance(Registries, list) == False:
                return Response("V1 provider require dockerRegistries", status=400)

        dockerRegistries = []
        for registry in Registries:
            registryname = registry['AccountName']
            if not base.is_account_exist("dockerRegistry",registryname):
                return Response("docker registry: {0} don't exist".format(registryname),
                         status=400)
            docker_dict = {"accountName":registryname, "namespaces":[]}
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
                "kubeconfigFile": kubeconfigFile,
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
        result = base.add_account("kubernetes",data)
    except Exception as e:
        logging.debug(e)
        return Response('Failed add the kubernetes provider', status=400)
    return result

@halyard.route("/halyard/addregistry", methods=['GET', 'POST'])
def add_docker_registry():
    try:
        p = request.json
        accountname = p['name']
        address = p['address']
        repositories = p['repositories']
        if p.has_key('username') and p.has_key('password'):
            username = p['username']
            password = p['password']
        else:
            username = None
            password = None

    except (KeyError, ValueError) as e:
        logging.debug(e)
        return Response('Invalid value in kubernetes yaml', status=400)

    try:
        if base.is_account_exist("dockerRegistry",accountname):
            return Response("account name has already exist", status=400)

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
        if result != "SUCCEEDED":
            return Response('Failed to add the docker registry', status=400)

    except Exception as e:
        logging.debug(e)
        return Response('Failed to add the docker registry', status=400)
    return result

@halyard.route("/halyard/delprovider", methods=['GET', 'POST'])
def delprovider():
    try:
        p = request.json
        provider = p['provider']
        name = p['name']
    except (KeyError, ValueError) as e:
        logging.debug(e)
        return Response('Input invalid value', status=400)
    try:
        result = base.delete_account(provider, name)
        if result != "SUCCEEDED":
            print "Delete account failed"
            return Response('Failed to delete the {0} provider'.format(provider), status=400)

        apply_result = base.apply_deploy()
        if apply_result != "SUCCEEDED":
            print "Delete account failed"
            return Response('Failed to delete the {0} provider'.format(provider), status=400)

    except Exception as e:
        logging.debug(e)
        return Response('Failed to delete the kubernetes provider', status=400)

    return apply_result


@halyard.route("/halyard/account", methods=['GET', 'POST'])
def getprovider():
    try:
        provider = ""
        p = request.json
        provider = p['name']
        account_list = base.list_accounts(provider)
        result = ':'.join(account_list)
    except Exception as e:
        logging.debug(e)
        return Response('get {0} failed'.format(provider), status=400)
    return result
