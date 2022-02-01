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

import logging
from time import sleep

from proxy.nginx import generate_nginx_configs
from proxy.endpoints import generate_endpoints
from proxy.helper import init_default_logger, write_json
from proxy.str_formatters import arguments_list_string
from proxy.config import (
    CHAINS_INFO_FILEPATH, MONITOR_INTERVAL, ENDPOINT, SM_ABI_FILEPATH, SERVER_NAME
)


logger = logging.getLogger(__name__)


def main():
    init_default_logger()
    logger.info(arguments_list_string({
        'Endpoint': ENDPOINT,
        'Server name': SERVER_NAME
        }, 'Starting SKALE Proxy server'))
    while True:
        logger.info('Collecting endpoints list')
        schains_endpoints = generate_endpoints(ENDPOINT, SM_ABI_FILEPATH)
        write_json(CHAINS_INFO_FILEPATH, schains_endpoints)
        generate_nginx_configs(schains_endpoints)
        logger.info(f'Proxy iteration done, sleeping for {MONITOR_INTERVAL}s...')
        sleep(MONITOR_INTERVAL)


if __name__ == '__main__':
    main()
