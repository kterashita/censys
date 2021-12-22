#!/usr/bin/env python3
"""
overall:
  input:
    - config
    - search query
  output:
    - formatted last-modified's value
      - "2018-10-09"
init_yaml:
  - create template config
main:
  - argparse
  - load config from yaml
  - create auth token by given apiid and secret
  hosts_search:
    - using censys api
    - https://search.censys.io/api#/hosts/searchHosts
    - api call by given search query
"""
import os
import re
import time
from base64 import b64encode
from datetime import datetime, timedelta
import argparse
import json
import yaml
import requests
import ipaddress
from tqdm import tqdm


init_yaml_filename = "config.yaml.init"

def get_argparse():
    parser = argparse.ArgumentParser(
        description="Help text of this command."
    )
    parser.add_argument('--initconfig', action='store_true', help="initalize config.yaml.init")
    parser.add_argument('-q', '--query', type=str, required=False, help="input query parameter")
    parser.add_argument('-c', '--config', type=str, required=False,
                        help="config yaml file")
    return parser.parse_args()


def init_yaml():
    """
    this creates default config template in init_yaml_filename.
    """

    init_yaml_filename = "config.yaml.init"

    init_yaml = {
        'censys': {
            'apiid': "",
            'secret': ""
        }
    }
    print("\033[34mSaved initial yaml config file: %s\033[0m" % str(init_yaml_filename))
    with open(init_yaml_filename, 'w') as f:
        yaml.dump(init_yaml, f)


def load_config(args):
    with open(args.config, 'r') as f:
        config_yaml = yaml.safe_load(f)
        #
        # PyYAML yaml.load(input) Deprecation
        # https://github.com/yaml/pyyaml/wiki/PyYAML-yaml.load(input)-Deprecation
        #
        # print(config_yaml['urlscanio']['apikey'])
    return config_yaml


def hosts_search(auth_token, args, config_dict):
    """
    expected input:
        search query parameter:
            - label: value    
    """

    api_base = 'https://search.censys.io/api'
    api_url = '/v2/hosts/search'

    headers = {
        'Accept': 'application/json',
        'Authorization': "Basic " + auth_token
        }
    
    # target url = https://search.censys.io/api/v2/hosts/search
    #     ?q=services.tls.certificates.leaf_data.subject.common_name%3A%20FGT60E**********&per_page=1&virtual_hosts=EXCLUDE

    # make query parameter fron config
    per_page = "1"
    virtual_hosts = "EXCLUDE"
    query = '?q=' + args.query + '&per_page=' + per_page + '&virtual_hosts=' + virtual_hosts

    api_url_full = api_base + api_url + query

    # call api
    response = requests.get(
        api_url_full,
        headers=headers
        )
    response_dict = response.json()
    
    return response_dict  # dict


def hosts_ip_return_ip(response_dict):
    # expose the first ip address from http response to dig futher
    ip = response_dict['result']['hits'][0]['ip']
    
    return ip


def host_ip(ip, auth_token):
    api_base = 'https://search.censys.io/api'
    api_url = '/v2/hosts/'
    api_url_full = api_base + api_url + ip

    headers = {
        'Accept': 'application/json',
        'Authorization': "Basic " + auth_token
        }
    
    # call api
    response = requests.get(
        api_url_full,
        headers=headers
        )
    response_dict = response.json()

    #
    # print(json.dumps(response_dict, indent=4))

    return response_dict


def get_http_last_modified(auth_token, args, config_dict):
    response_dict = hosts_search(auth_token, args, config_dict)
    ip = hosts_ip_return_ip(response_dict)
    ip_response_dict = host_ip(ip, auth_token)
    #
    # print(json.dumps(ip_response_dict['result']['services'], indent=4))
    
    # expose a readable last-modified value from each service port results
    for i in range(len(ip_response_dict['result']['services'])):
        try:
            print(json.dumps(ip_response_dict['result']['services'][i]['http']['response']['headers']['Last_Modified'][0], indent=4))
        except:
            pass


def main():
    args = get_argparse()
    if args.initconfig:
        init_yaml()
    if args.config:
        config_dict = load_config(args)
        auth_token = b64encode((config_dict['censys']['apiid'] + ':' + config_dict['censys']['secret']).encode('utf-8')).decode("ascii")
    else:
        print("You need config file.")
        exit()
    
    get_http_last_modified(auth_token, args, config_dict)


if __name__ == '__main__':
    main()