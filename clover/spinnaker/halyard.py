#!/bin/python


import requests
import json
import time
from clover.orchestration.kube_client import KubeClient

class Halyard:

    def __init__(self,
             base_url="http://spin-halyard.spinnaker:8064/v1", debug = False):
        self.base_url = base_url
        self.debug = debug
        self.client = KubeClient()
        self.namespace= 'spinnaker'
        self.headers = {'content-type': 'application/json; charset=UTF-8'}

    def _get(self, url):
        result = requests.get(url)
        return result.json()

    def _post(self, url, data = None, headers = None):
        result = requests.post(url, data=data, headers=headers)
        return result.json()

    def _put(self, url, data = None, headers = None):
        result = requests.put(url, data=data, headers=headers)
        return result.json()

    def _delete(self, url):
        result = requests.delete(url)
        return result.json()

    def _print_dict_info(self, dict_info, debug = False):
        if dict_info == None:
            return None

        if debug == True:
            for v,k in dict_info.items():
                print('{v}:{k}'.format(v = v, k = k))
        else:
            print dict_info.get('name')
            print dict_info.get('state')

    def is_account_exist(self, provider, accountname):
        exist_accounts = self.list_accounts(provider)
        if accountname in exist_accounts:
            print "account exists"
            return True
        print "account doesn't exist"
        return False

    def get_task_info(self, uuid):
        if uuid == None:
            return None
        url = self.base_url + "/tasks/" + uuid + "/"
        result = self._get(url)
        return result

    def wait_task_successful(self, uuid):
        flag = ""
        while True:
            resp = self.get_task_info(uuid)
            state = resp.get('state')
            if flag != state:
                self._print_dict_info(resp, self.debug)
                flag = state
            if state == "SUCCEEDED":
                return "SUCCEEDED", resp
            if state == "FAILED":
                return "FAILED", resp
            if resp.get('timedOut'):
                return "TimeOut", resp

    def get_current_deployment(self):
        '''get the current deployment and check the state'''

        url = self.base_url + "/config/currentDeployment"
        result = self._get(url)
        uuid = result.get('uuid')
        task_info = self.get_task_info(uuid)
        self._print_dict_info(task_info, self.debug)

        return task_info

    def apply_deploy(self):
        prep_url = self.base_url + \
                      "/config/deployments/default/prep/?validate=true"
        deploy_url = self.base_url + \
                      "/config/deployments/default/deploy/?validate=false"
        data='""'
        result = self._post(prep_url, data=data, headers=self.headers)
        uuid = result.get('uuid')
        result, task_info = self.wait_task_successful(uuid)
        if result != "SUCCEEDED":
            return result
        result = self._post(deploy_url, data=data, headers=self.headers)
        uuid = result.get('uuid')
        result, task_info = self.wait_task_successful(uuid)
        return result

    def list_accounts(self, provider, validate='true'):
        url = self.base_url + "/config/deployments/default/providers/" + \
                 provider + "/?validate=" + validate
        resp = self._get(url)
        uuid = resp.get('uuid')
        result, task_info = self.wait_task_successful(uuid)
        if result != "SUCCEEDED":
            print "Get account failed"
            return None
        accounts = task_info.get('response').get('responseBody').get('accounts')
        account_list = []
        for account in accounts:
            account_name = account.get('name')
            account_list.append(account_name)
        return account_list

    def enable_provider(self, provider, data='true', validate='true'):
        url = self.base_url + "/config/deployments/default/providers/" + \
                    provider + "/enabled/?validate=" + validate
        resp = self._put(url,data=data,headers=self.headers)
        uuid = resp.get('uuid')
        result, task_info = self.wait_task_successful(uuid)
        return result

    def add_account(self, provider, data, validate='true'):
        url = self.base_url + "/config/deployments/default/providers/" + \
                            provider + "/accounts/?validate=" + validate

        self.enable_provider(provider)

        resp = self._post(url, data=json.dumps(data), headers=self.headers)
        uuid = resp.get('uuid')
        result, task_info = self.wait_task_successful(uuid)
        if result != "SUCCEEDED":
            print "Add account failed"
            return result
        apply_result = self.apply_deploy()
        if apply_result == "SUCCEEDED":
            print "Deployment successful"
        else:
            print "Deployment failed"
        return apply_result

    def add_k8s_account(self, accountname, kubeconfigfile,
                    providerversion=None, registries=[], validate='true'):
        # Note: if providerversion is V1, must provider registries.
        if self.is_account_exist("kubernetes",accountname):
            return "FAILED"
        if providerversion == None or providerversion == 'V1':
            providerversion = None
            if 0 == len(registries) or isinstance(registries, list) == False:
                print "please provider docker registries or the type of registries is not list"
                return "FAILED"
        # Copy kubectl file to halyard pod
        hal_kubeconfigfile = "/home/spinnaker/config" + \
                     time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime())
        spinnaker_pods = self.client.find_pod_by_namespace(self.namespace)
        for pod in spinnaker_pods:
            if pod.find("spin-halyard") == 0:
                self.client.copy_file_to_pod(kubeconfigfile,
                                             hal_kubeconfigfile,
                                             pod, self.namespace)
        dockerRegistries = []
        for registry in registries:
            if not self.is_account_exist("dockerRegistry",registry):
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

        result = self.add_account("kubernetes",data)
        return result

    def add_docker_account(self, address, accountname, repositories=[],
                           username=None, password=None, validate='true'):

        if self.is_account_exist("dockerRegistry",accountname):
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
        result = self.add_account("dockerRegistry",data)
        if result == "SUCCEEDED":
            print "Add account successfully"
        else:
            print "Add account failed"
        return result

    def delete_account(self, provider, accountname, validate='true'):
        if not self.is_account_exist(provider, accountname):
            return "FAILED"
        url = self.base_url + "/config/deployments/default/providers/" + \
             provider + "/accounts/account/" + accountname + "/?validate=" + validate
        resp = self._delete(url)
        uuid = resp.get('uuid')
        result, task_info = self.wait_task_successful(uuid)
        if result != "SUCCEEDED":
            print "Delete account failed"
            return result

        apply_result = self.apply_deploy()
        if apply_result == "SUCCEEDED":
            print "Delete account successfully"
        else:
            print "Delete account failed"

        return apply_result


if __name__ == '__main__':
    test = Halyard()
