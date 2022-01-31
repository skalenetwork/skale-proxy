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

ENDPOINT = os.environ['ETH_ENDPOINT']
PORTS_PER_SCHAIN = 64

MONITOR_INTERVAL = os.getenv('MONITOR_INTERVAL', 60 * 60 * 2)

NGINX_WWW_FOLDER = '/www'
CHAINS_INFO_FILEPATH = os.path.join(NGINX_WWW_FOLDER, 'chains.json')

DATA_FOLDER = '/data'
SM_ABI_DEFAULT_FILEPATH = os.path.join(DATA_FOLDER, 'abi.json')
SM_ABI_FILEPATH = os.getenv('SM_ABI_FILEPATH', SM_ABI_DEFAULT_FILEPATH)
