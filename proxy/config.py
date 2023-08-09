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

DIR_PATH = os.path.dirname(os.path.realpath(__file__))
PROJECT_PATH = os.path.join(DIR_PATH, os.pardir)

ENDPOINT = os.environ['ETH_ENDPOINT']
PORTS_PER_SCHAIN = 64

MONITOR_INTERVAL = os.getenv('MONITOR_INTERVAL', 60 * 60 * 2)

NGINX_WWW_FOLDER = os.path.join(PROJECT_PATH, 'www')
CHAINS_INFO_FILEPATH = os.path.join(NGINX_WWW_FOLDER, 'chains.json')

DATA_FOLDER = os.path.join(PROJECT_PATH, 'data')

SM_ABI_DEFAULT_FILEPATH = os.path.join(DATA_FOLDER, 'abi.json')
SM_ABI_FILEPATH = os.getenv('SM_ABI_FILEPATH', SM_ABI_DEFAULT_FILEPATH)

TEMPLATES_FOLDER = os.path.join(PROJECT_PATH, 'templates')

SCHAIN_NGINX_TEMPLATE = os.path.join(TEMPLATES_FOLDER, 'chain.conf.j2')
UPSTREAM_NGINX_TEMPLATE = os.path.join(TEMPLATES_FOLDER, 'upstream.conf.j2')

CHAINS_FOLDER = os.path.join(PROJECT_PATH, 'conf', 'chains')
UPSTREAMS_FOLDER = os.path.join(PROJECT_PATH, 'conf', 'upstreams')

TMP_CHAINS_FOLDER = os.path.join(PROJECT_PATH, 'conf', 'tmp_chains')
TMP_UPSTREAMS_FOLDER = os.path.join(PROJECT_PATH, 'conf', 'tmp_upstreams')

SERVER_NAME = os.environ['SERVER_NAME']

PROXY_LOG_FORMAT = '[%(asctime)s] %(process)d %(levelname)s %(module)s: %(message)s'
LONG_LINE = '=' * 100

NGINX_CONTAINER_NAME = 'proxy_nginx'
CONTAINER_RUNNING_STATUS = 'running'

ALLOWED_TIMESTAMP_DIFF = 300