import time
import json
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
RESULTS_PATH = "/tmp/chains.json"
PROXY_FULL_HOST_NAME = os.environ.get("PROXY_FULL_HOST_NAME")

if PROXY_FULL_HOST_NAME is None:
    print("Fatal error: PROXY_FULL_HOST_NAME is not set. Exiting ...")
    exit(-3)

if not path.exists(CERT_FILE):
    print("Fatal error: could not find:" + CERT_FILE + " Exiting.")
    exit(-1)

if not path.exists(KEY_FILE):
    print("Fatal error: could not find:" + KEY_FILE + " Exiting.")
    exit(-2)


def parse_chains(_network: str, _path: str) -> list:
    json_file = open(_path,)
    parsed_json = json.load(json_file)

    chain_infos = list()

    for schain in parsed_json:
        name = schain["schain"][0]
        print("Schain name = ", name)
        nodes = schain["nodes"]

        list_of_http_endpoints = list()
        list_of_https_endpoints = list()

        for node in nodes:
            endpoint_http = node["http_endpoint_domain"]
            print("Http endpoint: " + endpoint_http)
            list_of_http_endpoints.append(endpoint_http)
            endpoint_https = node["https_endpoint_domain"]
            print(endpoint_https)
            list_of_https_endpoints.append(endpoint_https)

        chain_infos.append(ChainInfo(_network, name, list_of_http_endpoints, list_of_https_endpoints))

    return chain_infos


class ChainInfo:
    def __init__(self, _network: str, _chain_name: str, _list_of_http_endpoints: list,
                 _list_of_https_endpoints: list):
        self.network = _network
        self.chain_name = _chain_name
        self.list_of_http_endpoints = _list_of_http_endpoints
        self.list_of_https_endpoints = _list_of_https_endpoints


def run(_command) -> None:
    print(">" + _command)
    subprocess.check_call(_command, shell=True)


def print_global_server_config(_f, _use_ssl: bool) -> None:
    _f.write("server {\n")
    if _use_ssl:
        _f.write("	listen 443 ssl;\n")
        _f.write("	ssl_certificate " + CERT_FILE + ";\n")
        _f.write("  ssl_certificate_key " + KEY_FILE + ";\n")
        _f.write("	ssl_verify_client off;\n")
    else:
        _f.write("	listen 80;\n")
    _f.write("	root /usr/share/nginx/www;\n")
    _f.write("	index index.php index.html index.htm;\n")
    _f.write("	server_name " + PROXY_FULL_HOST_NAME + ";\n")


def print_group_definition(_chain_info: ChainInfo, _f) -> None:
    _f.write("upstream " + _chain_info.chain_name + " {\n")
    _f.write("   ip_hash;\n")
    for endpoint in _chain_info.list_of_http_endpoints:
        _f.write("   server " + endpoint[7:] + " max_fails=1 fail_timeout=600s;\n")
    _f.write("}\n")


def print_loadbalacing_config_for_chain(_chain_info: ChainInfo, _f) -> None:
    _f.write("	location /v1/" + _chain_info.chain_name + " {\n")
    # _f.write("	location /" + _chain_info.chain_name + " {\n")
    _f.write("	      proxy_http_version 1.1;\n")
    _f.write("	      proxy_pass http://" + _chain_info.chain_name + "/;\n")
    _f.write("	    }\n")


def print_config_file(_chain_infos: list) -> None:
    if os.path.exists(TMP_CONFIG_FILE):
        os.remove(TMP_CONFIG_FILE)
    with open(TMP_CONFIG_FILE, 'w') as f:
        for chain_info in _chain_infos:
            print_group_definition(chain_info, f)
        print_global_server_config(f, False)
        for chain_info in _chain_infos:
            print_loadbalacing_config_for_chain(chain_info, f)
        f.write("}\n")
        print_global_server_config(f, True)
        for chain_info in _chain_infos:
            print_loadbalacing_config_for_chain(chain_info, f)
        f.write("}\n")
        f.close()


def copy_config_file_if_modified() -> None:
    if (not path.exists(CONFIG_FILE)) or (not filecmp.cmp(CONFIG_FILE, TMP_CONFIG_FILE, shallow=False)):
        print("New config file. Reloading server")
        os.remove(CONFIG_FILE)
        copyfile(TMP_CONFIG_FILE, CONFIG_FILE)
        copyfile(TMP_CONFIG_FILE, CONFIG_FILE)
        run("/usr/sbin/nginx -s reload")


def main():
    while True:
        print("Updating chain info ...")
        subprocess.check_call(["/bin/bash", "-c", "rm -f /tmp/*"])
        subprocess.check_call(["/bin/bash", "-c",
                              "cp /etc/abi.json /tmp/abi.json"])
        subprocess.check_call(["python3", "/etc/endpoints.py"])
        subprocess.check_call(["/bin/bash", "-c", "mkdir -p /usr/share/nginx/www"])
        subprocess.check_call(["/bin/bash", "-c", "cp -f /tmp/chains.json /usr/share/nginx/www/chains.json"])

        if not os.path.exists(RESULTS_PATH):
            print("Fatal error: Chains file does not exist. Exiting ...")
            exit(-4)

        print("Generating config file ...")

        chain_infos = parse_chains("net", RESULTS_PATH)

        print("Checking Config file ")
        print_config_file(chain_infos)
        copy_config_file_if_modified()
        print("monitor loop iteration")
        sys.stdout.flush()
        time.sleep(6000)


# run main
main()
