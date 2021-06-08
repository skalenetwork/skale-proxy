#!/bin/bash
set -e
set -x

/usr/sbin/nginx &

while true
do
  sleep 30s
  rm -f /tmp/*
  python3 /etc/endpoints.py || true
  python3  /etc/periodic_config_update.py || true
  pgrep nginx
done



# start nginx

