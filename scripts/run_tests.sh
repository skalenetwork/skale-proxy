#!/usr/bin/env bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
PROJECT_DIR=$(dirname $DIR)
export ENDPOINT=${ENDPOINT:-http://localhost:8545}

python $PROJECT_DIR/tests/prepare_data.py
py.test $PROJECT_DIR/tests/ $@
