#!/bin/bash

set -e

export DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

: "${ENDPOINT?Need to set ENDPOINT}"
: "${MANAGER_TAG?Need to set MANAGER_TAG}"

cd $DIR/..
docker-compose up --build -d