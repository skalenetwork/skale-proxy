import time
import filecmp
import os
import os.path
import subprocess
from os import path

from shutil import copyfile


CONFIG_FILE = "/etc/nginx/sites-available/default"
TMP_CONFIG_FILE = "/tmp/tmp.config"


endpoints = list()

endpoints.append("testnet-16.skalenodes.com:10131")
endpoints.append("testnet-15.skalenodes.com:10195")


def print_loadbalacing_group(_endpoints, _f) :
    print("upstream backend {\n", _f)
    for endpoint in _endpoints:
        print("   server " + endpoint + ";\n", _f)
    print("}\n", _f)


def print_config_file(_endpoints):
    if os.path.exists(TMP_CONFIG_FILE):
        os.remove(TMP_CONFIG_FILE)
    with open(TMP_CONFIG_FILE, 'w') as f:
        print("server {\n", f)
        print("	listen 80;\n", f)
        print("	root /usr/share/nginx/www;\n", f)
        print("	index index.php index.html index.htm;\n", f)
        print("	server_name localhost;\n", f)
        print_loadbalacing_group(endpoints, f)
        print("	location /mainnet/chain1 {\n", f)
        print("	    proxy_http_version 1.1;\n", f)
        print("     proxy_pass http://backend/;\n", f)
        print("    }\n", f)
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
