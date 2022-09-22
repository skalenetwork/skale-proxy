#!/bin/bash

openssl req -newkey rsa:2048 -nodes -keyout ./data/server.key -x509 -days 365 -out ./data/server.crt
