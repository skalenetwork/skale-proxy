#!/bin/bash


rm -f /tmp/*
python3 /etc/endpoints.py
python3  /etc/periodic_config_update.py &

/usr/sbin/nginx

# start nginx

