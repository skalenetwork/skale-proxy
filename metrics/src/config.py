#   -*- coding: utf-8 -*-
#
#   This file is part of portal-metrics
#
#   Copyright (C) 2024 SKALE Labs
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

ERROR_TIMEOUT = os.getenv('MONITOR_INTERVAL', 60)
MONITOR_INTERVAL = os.getenv('MONITOR_INTERVAL', 10800)
NETWORK_NAME = os.getenv('NETWORK_NAME', 'mainnet')
ENDPOINT = os.environ['ETH_ENDPOINT']

PROXY_ENDPOINTS = {
    'mainnet': 'mainnet.skalenodes.com',
    'legacy': 'legacy-proxy.skaleserver.com',
    'regression': 'regression-proxy.skalenodes.com',
    'testnet': 'testnet.skalenodes.com',
}

BASE_EXPLORER_URLS = {
    'mainnet': 'explorer.mainnet.skalenodes.com',
    'legacy': 'legacy-explorer.skalenodes.com',
    'regression': 'regression-explorer.skalenodes.com',
    'testnet': 'explorer.testnet.skalenodes.com',
}
STATS_API = {'mainnet': 'https://stats.explorer.mainnet.skalenodes.com/v2/stats'}

HTTPS_PREFIX = 'https://'

BLOCK_SAMPLING = 100
GAS_ESTIMATION_ITERATIONS = 1

DIR_PATH = os.path.dirname(os.path.realpath(__file__))
PROJECT_PATH = os.path.join(DIR_PATH, os.pardir)

NGINX_WWW_FOLDER = os.path.join(PROJECT_PATH, 'www')
METRICS_FILEPATH = os.path.join(NGINX_WWW_FOLDER, 'metrics.json')

METRICS_CHECK_INTERVAL = 600
METRICS_ERROR_CHECK_INTERVAL = 30
API_ERROR_TIMEOUT = 2
API_ERROR_RETRIES = 3

GITHUB_RAW_URL = 'https://raw.githubusercontent.com'
OFFCHAIN_KEY = '__offchain'

DB_CONNECTION_RETRIES = 30
DB_CONNECTION_INTERVAL = 2

TRANSACTION_COUNT_FIELD = 'transactions_count'
BACKFILL_DB_DAYS = 30
