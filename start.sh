#!/bin/bash

python3  /etc/periodic_config_update.py &

# start nginx
/usr/sbin/nginx
