#!/bin/python


import requests
import json
import time

base_url="http://spin-halyard.spinnaker:8064/v1"
namespace= 'spinnaker'
headers = {'content-type': 'application/json; charset=UTF-8'}
debug = False

def get(url):
    result = requests.get(url)
    return result.json()

def post(url, data = None, headers = None):
    result = requests.post(url, data=data, headers=headers)
    return result.json()

def put(url, data = None, headers = None):
    result = requests.put(url, data=data, headers=headers)
    return result.json()

def delete(url):
    result = requests.delete(url)
    return result.json()

def print_dict_info(dict_info, debug = False):
    if dict_info == None:
        return None

    if debug == True:
        for v,k in dict_info.items():
            print('{v}:{k}'.format(v = v, k = k))
    else:
        print dict_info.get('name')
        print dict_info.get('state')

def is_account_exist(provider, accountname):
    exist_accounts = list_accounts(provider)
    if accountname in exist_accounts:
        print "account exists"
        return True
    print "account doesn't exist"
    return False

def get_task_info(uuid):
    if uuid == None:
        return None
    url = base_url + "/tasks/" + uuid + "/"
    result = get(url)
    return result

def wait_task_successful(uuid):
    flag = ""
    while True:
        resp = get_task_info(uuid)
        state = resp.get('state')
        if flag != state:
            print_dict_info(resp, debug)
            flag = state
        if state == "SUCCEEDED":
            return "SUCCEEDED", resp
        if state == "FAILED":
            return "FAILED", resp
        if resp.get('timedOut'):
            return "TimeOut", resp

def get_current_deployment():
    '''get the current deployment and check the state'''

    url = base_url + "/config/currentDeployment"
    result = get(url)
    uuid = result.get('uuid')
    task_info = get_task_info(uuid)
    print_dict_info(task_info, debug)

    return task_info

def apply_deploy():
    """
    after using api to config halyard, it need ruan apply deploy.
    """
    prep_url = base_url + "/config/deployments/default/prep/?validate=true"
    deploy_url = base_url + "/config/deployments/default/deploy/?validate=false"
    data='""'
    result = post(prep_url, data=data, headers=headers)
    uuid = result.get('uuid')
    result, task_info = wait_task_successful(uuid)
    if result != "SUCCEEDED":
        return result
    result = post(deploy_url, data=data, headers=headers)
    uuid = result.get('uuid')
    result, task_info = wait_task_successful(uuid)
    return result

def list_accounts(provider):
    """
    According to the provider, list all accounts
    """
    url = base_url + "/config/deployments/default/providers/" + \
             provider + "/?validate=true"
    resp = get(url)
    uuid = resp.get('uuid')
    result, task_info = wait_task_successful(uuid)
    if result != "SUCCEEDED":
        print "Get account failed"
        return None
    accounts = task_info.get('response').get('responseBody').get('accounts')
    account_list = []
    for account in accounts:
        account_name = account.get('name')
        account_list.append(account_name)
    return account_list

def enable_provider(provider, data='true'):
    """
    if needs to add a provider, it is necessary to enable the provider
    """
    url = base_url + "/config/deployments/default/providers/" + \
                provider + "/enabled/?validate=true"
    resp = put(url,data=data,headers=headers)
    uuid = resp.get('uuid')
    result, task_info = wait_task_successful(uuid)
    return result

def add_account(provider, data):
    url = base_url + "/config/deployments/default/providers/" + \
                        provider + "/accounts/?validate=true"

    enable_provider(provider)

    resp = post(url, data=json.dumps(data), headers=headers)
    uuid = resp.get('uuid')
    result, task_info = wait_task_successful(uuid)
    if result != "SUCCEEDED":
        print "Add account failed"
        return result
    apply_result = apply_deploy()
    if apply_result == "SUCCEEDED":
        print "Deployment successful"
    else:
        print "Deployment failed"
    return apply_result

def delete_account(provider, accountname):
    if not is_account_exist(provider, accountname):
        return "FAILED"
    url = base_url + "/config/deployments/default/providers/" + \
         provider + "/accounts/account/" + accountname + "/?validate=true"
    resp = delete(url)
    uuid = resp.get('uuid')
    result, task_info = wait_task_successful(uuid)

    return result

