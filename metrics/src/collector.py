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

import json
import logging
import asyncio
import aiohttp
from datetime import datetime, date, timedelta
from typing import Tuple, Optional, Dict, List
from aiohttp import ClientError, ClientSession

from src.explorer import get_address_counters_url, get_chain_stats
from src.gas import calc_avg_gas_price
from src.db import update_transaction_counts, get_address_transaction_counts
from src.utils import transform_to_dict, decimal_default
from src.config import (
    METRICS_FILEPATH,
    API_ERROR_TIMEOUT,
    API_ERROR_RETRIES,
    GITHUB_RAW_URL,
    OFFCHAIN_KEY,
)
from src.metrics_types import (
    AddressCounter,
    AddressCountersMap,
    MetricsData,
    ChainMetrics,
    AddressType,
)

logger = logging.getLogger(__name__)


async def download_metadata(session: ClientSession, network_name: str) -> Dict:
    """Download and parse network metadata."""
    url = f'{GITHUB_RAW_URL}/skalenetwork/skale-network/master/metadata/{network_name}/chains.json'
    async with session.get(url) as response:
        metadata_str = await response.text()
        return json.loads(metadata_str)


def get_empty_address_counter() -> AddressCounter:
    """Return an empty counter structure with zero values."""
    return {
        'gas_usage_count': '0',
        'token_transfers_count': '0',
        'transactions_count': '0',
        'validations_count': '0',
        'transactions_today': 0,
        'transactions_last_7_days': 0,
        'transactions_last_30_days': 0,
    }


async def fetch_address_data(
    session: ClientSession, url: str, chain_name: str, app_name: str, address: str
) -> AddressCounter:
    """Fetch and process address data, updating DB immediately."""
    async with session.get(url) as response:
        if response.status == 404:
            data = await response.json()
            if data.get('message') == 'Not found':
                logger.warning(f'Address not found at {url}. Returning empty counter.')
                return get_empty_address_counter()
        response.raise_for_status()

        current_data: Dict = await response.json()
        logger.debug(f'Explorer response for {address}: {json.dumps(current_data, indent=2)}')

        await update_transaction_counts(chain_name, app_name, address, current_data)
        result = await get_db_counts(current_data, chain_name, app_name, address)
        logger.info(f'Fetched data for {address} at {url}: {result}')
        return result


async def get_db_counts(
    current_data: Dict, chain_name: str, app_name: str, address: str
) -> AddressCounter:
    today = date.today()
    tomorrow = today + timedelta(days=1)
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)

    transactions_today = await get_address_transaction_counts(
        chain_name, app_name, address, today, tomorrow
    )
    transactions_last_7_days = await get_address_transaction_counts(
        chain_name, app_name, address, week_ago, today
    )
    transactions_last_30_days = await get_address_transaction_counts(
        chain_name, app_name, address, month_ago, today
    )
    return {
        'gas_usage_count': str(current_data.get('gas_usage_count', '0')),
        'token_transfers_count': str(current_data.get('token_transfers_count', '0')),
        'transactions_count': str(current_data.get('transactions_count', '0')),
        'validations_count': str(current_data.get('validations_count', '0')),
        'transactions_today': transactions_today,
        'transactions_last_7_days': transactions_last_7_days,
        'transactions_last_30_days': transactions_last_30_days,
    }


async def get_address_counters(
    session: ClientSession, network: str, chain_name: str, app_name: str, address: str
) -> AddressCounter:
    """Get address counters with retries."""
    url = get_address_counters_url(network, chain_name, address)

    for attempt in range(API_ERROR_RETRIES):
        try:
            return await fetch_address_data(session, url, chain_name, app_name, address)
        except ClientError as e:
            if attempt < API_ERROR_RETRIES - 1:
                logger.warning(f'Attempt {attempt + 1} failed for {url}. Retrying... Error: {e}')
                await asyncio.sleep(API_ERROR_TIMEOUT)
            else:
                logger.error(f'All attempts failed for {url}. Error: {e}')
                raise
    raise Exception(f'Failed to fetch data for {url}')


async def get_all_address_counters(
    session: ClientSession, network: str, chain_name: str, app_name: str, addresses: List[str]
) -> AddressCountersMap:
    """Get counters for multiple addresses concurrently."""
    tasks = [
        get_address_counters(session, network, chain_name, app_name, address)
        for address in addresses
    ]
    results = await asyncio.gather(*tasks)
    return {AddressType(addr): counter for addr, counter in zip(addresses, results)}


async def fetch_counters_for_app(
    session: ClientSession, network_name: str, chain_name: str, app_name: str, app_info: Dict
) -> Tuple[str, Optional[AddressCountersMap]]:
    """Fetch counters for a specific app."""
    logger.info(f'Fetching counters for app {app_name}')
    if 'contracts' in app_info:
        counters = await get_all_address_counters(
            session, network_name, chain_name, app_name, app_info['contracts']
        )
        return app_name, counters
    return app_name, None


async def fetch_counters_for_apps(
    session: ClientSession, chain_info: Dict, network_name: str, chain_name: str
) -> List[Tuple[str, Optional[AddressCountersMap]]]:
    """Fetch counters for all apps in a chain concurrently."""
    tasks = [
        fetch_counters_for_app(session, network_name, chain_name, app_name, app_info)
        for app_name, app_info in chain_info['apps'].items()
    ]
    return await asyncio.gather(*tasks)


async def collect_metrics(network_name: str) -> MetricsData:
    """Collect all metrics and save to file."""
    async with aiohttp.ClientSession() as session:
        metadata = await download_metadata(session, network_name)
        metrics: Dict[str, ChainMetrics] = {}

        for chain_name, chain_info in metadata.items():
            logger.info(f'Collecting metrics for chain {chain_name}...')
            if chain_name == OFFCHAIN_KEY:
                continue
            try:
                chain_stats = await get_chain_stats(session, network_name, chain_name)
                if chain_stats is None:
                    logger.warning(f'No chain stats available for {chain_name}. Skipping.')
                    continue

                apps_counters = None
                if 'apps' in chain_info:
                    apps_counters = await fetch_counters_for_apps(
                        session, chain_info, network_name, chain_name
                    )

                metrics[chain_name] = {
                    'chain_stats': chain_stats,
                    'apps_counters': transform_to_dict(apps_counters),
                }
            except Exception as e:
                logger.exception(f'Error collecting metrics for chain {chain_name}: {e}')
                continue

        data: MetricsData = {
            'metrics': metrics,
            'gas': int(calc_avg_gas_price()),
            'last_updated': int(datetime.now().timestamp()),
        }

        logger.info(f'Saving metrics to {METRICS_FILEPATH}')
        with open(METRICS_FILEPATH, 'w') as f:
            json.dump(data, f, indent=4, sort_keys=True, default=decimal_default)

        return data
