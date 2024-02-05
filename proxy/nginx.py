#   -*- coding: utf-8 -*-
#
#   This file is part of SKALE Proxy
#
#   Copyright (C) 2022-Present SKALE Labs
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Affero General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public License
#   along with this program.  If not, see <https://www.gnu.org/licenses/>.

import os
import shutil
import logging
from pathlib import Path

import docker

from proxy.helper import process_template
from proxy.config import (
    SCHAIN_NGINX_TEMPLATE, UPSTREAM_NGINX_TEMPLATE, CHAINS_FOLDER, UPSTREAMS_FOLDER,
    NGINX_CONTAINER_NAME, CONTAINER_RUNNING_STATUS, TMP_CHAINS_FOLDER, TMP_UPSTREAMS_FOLDER
)


logger = logging.getLogger(__name__)
docker_client = docker.DockerClient()


def update_nginx_configs(schains_endpoints: list) -> None:
    generate_nginx_configs(schains_endpoints)
    move_nginx_configs()
    monitor_nginx_container()


def move_nginx_configs():
    """Moves nginx configs from the temporary directories to the main folders"""
    logger.info('Moving nginx configs from temporary directories...')
    shutil.rmtree(CHAINS_FOLDER, ignore_errors=True)
    shutil.rmtree(UPSTREAMS_FOLDER, ignore_errors=True)
    shutil.move(TMP_CHAINS_FOLDER, CHAINS_FOLDER)
    shutil.move(TMP_UPSTREAMS_FOLDER, UPSTREAMS_FOLDER)
    Path(TMP_CHAINS_FOLDER).mkdir(parents=True, exist_ok=True)
    Path(TMP_UPSTREAMS_FOLDER).mkdir(parents=True, exist_ok=True)
    logger.info('nginx configs moved')


def monitor_nginx_container(d_client=None):
    logger.info('Going to restart nginx container')
    d_client = d_client or docker_client
    nginx_container = d_client.containers.get(NGINX_CONTAINER_NAME)

    if is_container_running(nginx_container):
        reload_nginx(nginx_container)
    else:
        logger.info('nginx container is not running, trying to restart')
        nginx_container.restart()


def reload_nginx(container) -> int:
    res = container.exec_run(cmd='nginx -s reload')
    if res != 0:
        logger.warning('Could not reload nginx configuration, check out nginx logs')
    else:
        logger.info('Successfully reloaded nginx service')
    return res


def is_container_running(container) -> bool:
    return container.status == CONTAINER_RUNNING_STATUS


def generate_nginx_configs(schains_endpoints: list) -> None:
    logger.info('Generating nginx configs...')
    for schain_endpoints in schains_endpoints:
        if not schain_endpoints:
            continue
        logger.info(f'Processing template for {schain_endpoints["chain_info"]["schain_name"]}...')
        process_nginx_config_template(schain_endpoints['chain_info'])


def process_nginx_config_template(chain_info: dict) -> None:
    chain_dest = os.path.join(TMP_CHAINS_FOLDER, f'{chain_info["schain_name"]}.conf')
    upstream_dest = os.path.join(TMP_UPSTREAMS_FOLDER, f'{chain_info["schain_name"]}.conf')
    process_template(SCHAIN_NGINX_TEMPLATE, chain_dest, chain_info)
    process_template(UPSTREAM_NGINX_TEMPLATE, upstream_dest, chain_info)


if __name__ == '__main__':
    res = generate_nginx_configs([])
    print(res)
