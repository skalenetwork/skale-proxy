#!/bin/bash

set -e

export DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

: "${ENDPOINT?Need to set ENDPOINT}"

cd $DIR/..
docker-compose up --build -d