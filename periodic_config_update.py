import time
import filecmp
import os
import os.path
import subprocess
from os import path

from shutil import copyfile


CONFIG_FILE = "/etc/nginx/sites-available/default"
TMP_CONFIG_FILE = "/tmp/tmp.config"


def print_config_file():
    if os.path.exists(TMP_CONFIG_FILE):
        os.remove(TMP_CONFIG_FILE)
    with open(TMP_CONFIG_FILE, 'w') as f:
        print("upstream backend {\n", f)
        print("   server testnet-16.skalenodes.com:10131;\n", f)
        print("   server testnet-15.skalenodes.com:10195;\n", f)
        print("}\n", f)
        print("server {\n", f)
        print("	listen 80;\n", f)
        print("	root /usr/share/nginx/www;\n", f)
        print("	index index.php index.html index.htm;\n", f)
        print("	server_name localhost;\n", f)
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
    print_config_file()
    copy_config_file_if_modified()
    time.sleep(5)
    print("loop")
