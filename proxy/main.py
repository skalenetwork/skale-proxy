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
from proxy.endpoints import endpoints_for_all_schains
from proxy.helper import write_json
from proxy.config import CHAINS_INFO_FILEPATH, MONITOR_INTERVAL, ENDPOINT, SM_ABI_FILEPATH


logger = logging.getLogger(__name__)


def main():
    logger.info('Starting SKALE Proxy server')
    while True:
        logger.info('Collecting endpoints list')
        endpoints = endpoints_for_all_schains(ENDPOINT, SM_ABI_FILEPATH)
        write_json(CHAINS_INFO_FILEPATH, endpoints)

        generate_nginx_configs(endpoints)

        logger.info(f'Proxy iteration done, sleeping for {MONITOR_INTERVAL}')
        sleep(MONITOR_INTERVAL)


if __name__ == '__main__':
    main()
