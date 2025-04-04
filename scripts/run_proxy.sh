#!/bin/bash

set -e

# Ensure required variables are set
: "${ETH_ENDPOINT?Need to set ETH_ENDPOINT}"
# Default USE_ELB to 'false' if not explicitly set. Controls whether to keep the 
# ELB (Elastic Load Balancer) block  to fix real origin IP in the Nginx config.
: "${USE_ELB:=False}"

# Determine script directory and project root
export SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
PROJECT_DIR=$(dirname $SCRIPT_DIR)

##### ELASTICSEARCH CONFIGURATION START #####

# Define file paths relative to project root.
CONFIG_DIR="$PROJECT_DIR/config"
TEMPLATE_FILE="$CONFIG_DIR/nginx.conf.template" # Using a separate template file
TARGET_FILE="$CONFIG_DIR/nginx.conf" # File Docker Compose will mount

# Define the markers for the real IP configuration block.
# These should be present in the template file to identify the start and end
# of the block to be removed.
START_MARKER="#REAL_IP_CONFIG_START"
END_MARKER="#REAL_IP_CONFIG_END"

# Check if template file exists.
if [ ! -f "$TEMPLATE_FILE" ]; then
    echo "ERROR: Nginx template file not found at $TEMPLATE_FILE"
    exit 1
fi

if [[ "$USE_ELB" == "True" ]]; then
    # ELB mode enabled. Nginx configuration block will remain.
    # Copy the template directly, it already has the config block.
    cp "$TEMPLATE_FILE" "$TARGET_FILE"
else
    # ELB mode disabled. Remove real IP configuration block from template.
    # Use sed to delete the block between the markers (inclusive) and write to target
    sed "/${START_MARKER}/,/${END_MARKER}/d" "$TEMPLATE_FILE" > "$TARGET_FILE"
fi

# Proceed with docker compose (original script logic)
cd "$PROJECT_DIR"
docker compose up --build -d