import time
import filecmp
import os
import sys
import os.path
import subprocess
from os import path
from shutil import copyfile


class ChainInfo:
    def __init__(self, _chain_name, _list_of_domain_endpoints):
        self.chain_name = _chain_name
        self.list_of_domain_endpoints = _list_of_domain_endpoints


def run(_command):
    print(">" + _command)
    subprocess.check_call(_command, shell=True)


def print_global_server_config(_f):
    print("server {\n", _f)
    print("	listen 80;\n", _f)
    print("	root /usr/share/nginx/www;\n", _f)
    print("	index index.php index.html index.htm;\n", _f)
    print("	server_name localhost;\n", _f)


def print_loadbalacing_config_for_chain(_chain_info: ChainInfo, _f):
    print("upstream " + _chain_info.chain_name + " {\n", _f)
    for endpoint in _chain_info.list_of_domain_endpoints:
        print("   server " + endpoint + ";\n", _f)
    print("}\n", _f)
    print("	location /mainnet/" + _chain_info.chain_name + "{\n", _f)
    print("	    proxy_http_version 1.1;\n", _f)
    print("     proxy_pass http://" + _chain_info.chain_name + "/;\n", _f)
    print("    }\n", _f)


def print_config_file(_chain_infos: list):
    if os.path.exists(TMP_CONFIG_FILE):
        os.remove(TMP_CONFIG_FILE)
    with open(TMP_CONFIG_FILE, 'w') as f:
        print_global_server_config(f)
        for chain_info in _chain_infos:
            print_loadbalacing_config_for_chain(chain_info, f)
        print("}\n", f)


def copy_config_file_if_modified():
    if (not path.exists(CONFIG_FILE)) or (not filecmp.cmp(CONFIG_FILE, TMP_CONFIG_FILE, shallow=False)):
        print("New config file. Reloading server", file=sys.stderr)
        os.remove(CONFIG_FILE)
        copyfile(TMP_CONFIG_FILE, CONFIG_FILE)
        run("/usr/sbin/nginx -s reload")


CONFIG_FILE = "/etc/nginx/sites-available/default"
TMP_CONFIG_FILE = "/tmp/tmp.config"

endpoints = list()
endpoints.append("testnet-16.skalenodes.com:10131")
endpoints.append("testnet-15.skalenodes.com:10195")

chain_infos = list()

# TODO: get real list here

chain_info = ChainInfo("chain1", endpoints)
chain_infos.append(chain_info)

# let nginx start)
time.sleep(10)

while True:
    print("Checking Config file ")
    print_config_file(chain_infos)
    copy_config_file_if_modified()
    print("monitor loop iteration")
    sys.stdout.flush()
    time.sleep(20)
