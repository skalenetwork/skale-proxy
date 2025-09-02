#   -*- coding: utf-8 -*-
#
#   This file is part of SKALE Proxy
#
#   Copyright (C) 2024-Present SKALE Labs
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
import requests

logger = logging.getLogger(__name__)


def send_heartbeat(heartbeat_url):
    if heartbeat_url:
        try:
            response = requests.get(heartbeat_url, timeout=10)
            if response.status_code == 200:
                logger.info('Heartbeat signal is successfully sent')
            else:
                logger.warning(f'Failed to send heartbeat signal: {response.status_code}')
        except Exception as e:
            logger.error(f'Failed to send heartbeat signal: {e}')
    else:
        logger.info('HEARTBEAT_URL is not set or empty')
