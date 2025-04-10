#!/bin/bash

set -e

: "${ETH_ENDPOINT?Need to set ETH_ENDPOINT}"
: "${USE_ALB:=False}"

export SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
PROJECT_DIR=$(dirname $SCRIPT_DIR)

CONFIG_DIR="$PROJECT_DIR/config"
TEMPLATE_FILE="$CONFIG_DIR/nginx.conf.template"
TARGET_FILE="$CONFIG_DIR/nginx.conf"

START_MARKER="#REAL_IP_CONFIG_START"
END_MARKER="#REAL_IP_CONFIG_END"

if [ ! -f "$TEMPLATE_FILE" ]; then
    echo "ERROR: Nginx template file not found at $TEMPLATE_FILE"
    exit 1
fi

if [[ "$USE_ALB" == "True" ]]; then
    cp "$TEMPLATE_FILE" "$TARGET_FILE"
else
    # Remove the ALB real IP configuration block between markers from the template
    sed "/${START_MARKER}/,/${END_MARKER}/d" "$TEMPLATE_FILE" > "$TARGET_FILE"
fi

cd "$PROJECT_DIR"
docker compose up --build -d
