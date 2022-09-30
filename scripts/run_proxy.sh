#!/bin/bash

export DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

export NETWORKS=$NETWORKS
export DOCS_WEBSITE_URL=$DOCS_WEBSITE_URL
export MAIN_WEBSITE_URL=$MAIN_WEBSITE_URL
export NETWORK_NAME=$NETWORK_NAME
export CHAIN_ID=$CHAIN_ID
export EXPLORER_URL=$EXPLORER_URL
export BASE_PROXY_URL=$BASE_PROXY_URL
export ABIS_URL=$ABIS_URL

bash $DIR/../network-ui/prepare_env_file.sh

cd $DIR/..
docker-compose up --build -d