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
import logging

import docker

from proxy.helper import process_template
from proxy.config import (
    SCHAIN_NGINX_TEMPLATE, UPSTREAM_NGINX_TEMPLATE, CHAINS_FOLDER, UPSTREAMS_FOLDER, SERVER_NAME,
    NGINX_CONTAINER_NAME
)


logger = logging.getLogger(__name__)
docker_client = docker.DockerClient()


def update_nginx_configs(schains_endpoints: list) -> None:
    generate_nginx_configs(schains_endpoints)
    restart_nginx_container()


def restart_nginx_container(d_client=None):
    logger.info('Going to restart nginx container')
    d_client = d_client or docker_client
    nginx_container = d_client.containers.get(NGINX_CONTAINER_NAME)
    nginx_container.restart()
    logger.info('Successfully restarted nginx container')


def generate_nginx_configs(schains_endpoints: list) -> None:
    logger.info('Generating nginx configs...')
    for schain_endpoints in schains_endpoints:
        logger.info(f'Processing template for {schain_endpoints["chain_info"]["schain_name"]}...')
        process_nginx_config_template(schain_endpoints['chain_info'], SERVER_NAME)


def process_nginx_config_template(chain_info: dict, server_name: str) -> None:
    chain_dest = os.path.join(CHAINS_FOLDER, f'{chain_info["schain_name"]}.conf')
    upstream_dest = os.path.join(UPSTREAMS_FOLDER, f'{chain_info["schain_name"]}.conf')
    chain_info['server_name'] = server_name
    process_template(SCHAIN_NGINX_TEMPLATE, chain_dest, chain_info)
    process_template(UPSTREAM_NGINX_TEMPLATE, upstream_dest, chain_info)


if __name__ == '__main__':
    chain_data = {'schain_name': 'test'}
    process_nginx_config_template({
        'server_name': 'test.com',
        'schain_name': 'test',
        'http_endpoints': ['ssss.com:15555', 'aaaa', 'bbbbb'],
        'ws_endpoints': ['fgdfgdf', 'dsgfs', 'asaffd'],
        'fs_endpoints': ['bvf', 'g', 'hh'],
    })
