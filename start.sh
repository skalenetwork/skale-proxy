#!/bin/bash

python3  /etc/periodic_config_update.py &

# start all the services
/usr/local/bin/supervisord -n
