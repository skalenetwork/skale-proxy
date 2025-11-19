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

from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    endpoint: str
    manager_contracts: str
    network_name: str

    heartbeat_url: str | None = None

    monitor_interval: int = 10 * 60
    error_retry_interval: int = 30

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=False,
        extra='ignore',
    )


def get_config() -> Config:
    return Config()  # type: ignore[call-arg]


DIR_PATH = os.path.dirname(os.path.realpath(__file__))
PROJECT_PATH = os.path.join(DIR_PATH, os.pardir)

NGINX_WWW_FOLDER = os.path.join(PROJECT_PATH, 'www')
CHAINS_INFO_FILEPATH = os.path.join(NGINX_WWW_FOLDER, 'chains.json')

DATA_FOLDER = os.path.join(PROJECT_PATH, 'data')
TEMPLATES_FOLDER = os.path.join(PROJECT_PATH, 'templates')

SCHAIN_NGINX_TEMPLATE = os.path.join(TEMPLATES_FOLDER, 'chain.conf.j2')
UPSTREAM_NGINX_TEMPLATE = os.path.join(TEMPLATES_FOLDER, 'upstream.conf.j2')

CHAINS_FOLDER = os.path.join(PROJECT_PATH, 'conf', 'chains')
UPSTREAMS_FOLDER = os.path.join(PROJECT_PATH, 'conf', 'upstreams')

TMP_CHAINS_FOLDER = os.path.join(PROJECT_PATH, 'conf', 'tmp_chains')
TMP_UPSTREAMS_FOLDER = os.path.join(PROJECT_PATH, 'conf', 'tmp_upstreams')

PROXY_LOG_FORMAT = '[%(asctime)s] %(process)d %(levelname)s %(module)s: %(message)s'
LONG_LINE = '=' * 100

NGINX_CONTAINER_NAME = 'proxy_nginx'
CONTAINER_RUNNING_STATUS = 'running'

ALLOWED_TIMESTAMP_DIFF = 300

GITHUB_RAW_URL = 'https://raw.githubusercontent.com'
