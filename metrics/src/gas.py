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

import logging

from web3 import Web3

from src.config import BLOCK_SAMPLING, ENDPOINT, GAS_ESTIMATION_ITERATIONS

logger = logging.getLogger(__name__)


def init_w3():
    logger.info(f'Connecting to {ENDPOINT}...')
    return Web3(Web3.HTTPProvider(ENDPOINT))


def calc_avg_gas_price():
    block_num = GAS_ESTIMATION_ITERATIONS * BLOCK_SAMPLING
    logger.info(f'Calculating average gas price for the last {block_num} blocks')
    w3 = init_w3()
    block_number = w3.eth.block_number
    total_gas_used = 0

    logger.info('Getting historic block gas prices...')
    for index in range(GAS_ESTIMATION_ITERATIONS):
        block_number = block_number - BLOCK_SAMPLING * index
        if block_number < 0:
            break
        logger.info(f'Getting block {block_number}...')
        block = w3.eth.get_block(block_number)
        total_gas_used += block['baseFeePerGas']

    avg_gas_price = int(total_gas_used / GAS_ESTIMATION_ITERATIONS)
    logger.info(f'avg_gas_price: {avg_gas_price}')
    return avg_gas_price
