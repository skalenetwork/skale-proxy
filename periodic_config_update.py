import time
import filecmp
import os
import os.path
import subprocess
from os import path

from shutil import copyfile


CONFIG_FILE = "/etc/nginx/sites-available/default"
TMP_CONFIG_FILE = "/tmp/tmp.config"


class ChainInfo:
    def __init__(self, _chain_name, _list_of_domain_endpoints):
        self.chain_name = _chain_name
        self.list_of_domain_endpoints = _list_of_domain_endpoints


endpoints = list()
endpoints.append("testnet-16.skalenodes.com:10131")
endpoints.append("testnet-15.skalenodes.com:10195")

chain_info = ChainInfo("chain1", endpoints)


def print_loadbalacing_group(_chain_info : ChainInfo, _f):
    print("upstream " + _chain_info.chain_name + " {\n", _f)
    for endpoint in _chain_info.list_of_domain_endpoints:
        print("   server " + endpoint + ";\n", _f)
    print("}\n", _f)
    print("	location /mainnet/" + _chain_info.chain_name + "{\n", _f)
    print("	    proxy_http_version 1.1;\n", _f)
    print("     proxy_pass http://" + _chain_info.chain_name + "/;\n", _f)
    print("    }\n", _f)


def print_config_file(_chain_info):
    if os.path.exists(TMP_CONFIG_FILE):
        os.remove(TMP_CONFIG_FILE)
    with open(TMP_CONFIG_FILE, 'w') as f:
        print("server {\n", f)
        print("	listen 80;\n", f)
        print("	root /usr/share/nginx/www;\n", f)
        print("	index index.php index.html index.htm;\n", f)
        print("	server_name localhost;\n", f)
        print_loadbalacing_group(_chain_info, f)
        print("}\n", f)


def run(_command):
    print(">" + _command)
    subprocess.check_call(_command, shell=True)


def copy_config_file_if_modified():
    if (not path.exists(CONFIG_FILE)) or (not filecmp.cmp(CONFIG_FILE, TMP_CONFIG_FILE, shallow=False)):
        os.remove(CONFIG_FILE)
        copyfile(TMP_CONFIG_FILE, CONFIG_FILE)
        run("/usr/sbin/nginx -s reload")


while True:
    print_config_file(endpoints)
    copy_config_file_if_modified()
    time.sleep(5)
    print("loop")
