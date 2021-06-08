#!/bin/bash
set -e
set -x


python3  /etc/periodic_config_update.py &

/usr/sbin/nginx




# start nginx

