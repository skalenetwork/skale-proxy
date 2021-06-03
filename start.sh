#!/bin/bash
#  /usr/bin/mysqld_safe &
  sleep 10s

# start all the services
/usr/local/bin/supervisord -n
