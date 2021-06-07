import time
import filecmp
import os
import sys
import os.path
import subprocess
from os import path
from shutil import copyfile

CONFIG_FILE = "/etc/nginx/sites-available/default"
TMP_CONFIG_FILE = "/tmp/tmp.config"
CERT_FILE = "/data/server.crt"
KEY_FILE = "/data/server.key"


class ChainInfo:
    def __init__(self, _network: str, _chain_name: str, _list_of_domain_endpoints: list):
        self.network = _network
        self.chain_name = _chain_name
        self.list_of_domain_endpoints = _list_of_domain_endpoints


def run(_command):
    print(">" + _command)
    subprocess.check_call(_command, shell=True)


def print_global_server_config(_f, _use_ssl: bool):
    _f.write("server {\n")
    if _use_ssl:
        _f.write("	listen 443 ssl;\n")
        _f.write("	ssl_certificate " + CERT_FILE + "\n")
        _f.write("  ssl_certificate_key " + KEY_FILE + "\n")
        _f.write("	ssl_verify_client off;\n")
    else:
        _f.write("	listen 80;\n")
    _f.write("	root /usr/share/nginx/www;\n")
    _f.write("	index index.php index.html index.htm;\n")
    _f.write("	server_name localhost;\n")


def print_group_definition(_chain_info: ChainInfo, _f):
    _f.write("upstream " + _chain_info.chain_name + " {\n")
    _f.write("   ip_hash;\n")
    for endpoint in _chain_info.list_of_domain_endpoints:
        _f.write("   server " + endpoint + " max_fails=1 fail_timeout=600s;\n")
    _f.write("}\n")


def print_loadbalacing_config_for_chain(_chain_info: ChainInfo, _f):
    _f.write("	location /"+_chain_info.network + "/" + _chain_info.chain_name + " {\n")
    _f.write("	      proxy_http_version 1.1;\n")
    _f.write("	      proxy_pass http://" + _chain_info.chain_name + "/;\n")
    _f.write("	    }\n")


def print_config_file(_chain_infos: list):
    if os.path.exists(TMP_CONFIG_FILE):
        os.remove(TMP_CONFIG_FILE)
    with open(TMP_CONFIG_FILE, 'w') as f:
        for chain_info in _chain_infos:
            print_group_definition(chain_info, f)
        print_global_server_config(f, False)
        for chain_info in _chain_infos:
            print_loadbalacing_config_for_chain(chain_info, f)
        print_global_server_config(f, True)
        for chain_info in _chain_infos:
            print_loadbalacing_config_for_chain(chain_info, f)
        f.write("}\n")
        f.close()


def copy_config_file_if_modified():
    if (not path.exists(CONFIG_FILE)) or (not filecmp.cmp(CONFIG_FILE, TMP_CONFIG_FILE, shallow=False)):
        print("New config file. Reloading server")
        os.remove(CONFIG_FILE)
        copyfile(TMP_CONFIG_FILE, CONFIG_FILE)
        copyfile(TMP_CONFIG_FILE, CONFIG_FILE)
        run("/usr/sbin/nginx -s reload")


endpoints = list()
endpoints.append("testnet-16.skalenodes.com:10131")
endpoints.append("testnet-15.skalenodes.com:10195")

chain_infos = list()

# TODO: get real list here

chain_info = ChainInfo("mainnet", "chain1", endpoints)
chain_infos.append(chain_info)

# let nginx start)


time.sleep(30)

if not path.exists(CERT_FILE):
    print("Fatal error: could not find:" + CERT_FILE + " Exiting.")
    exit(-1)

if not path.exists(KEY_FILE):
    print("Fatal error: could not find:" + KEY_FILE + " Exiting.")
    exit(-2)

while True:
    print("Checking Config file ")
    print_config_file(chain_infos)
    copy_config_file_if_modified()
    print("monitor loop iteration")
    sys.stdout.flush()
    time.sleep(20)
