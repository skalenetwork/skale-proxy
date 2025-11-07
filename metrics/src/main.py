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

import asyncio
import logging
import sys
from datetime import datetime
from time import sleep

import aiohttp

from src.collector import collect_metrics, download_metadata
from src.config import (
    DB_CONNECTION_INTERVAL,
    DB_CONNECTION_RETRIES,
    METRICS_CHECK_INTERVAL,
    METRICS_ERROR_CHECK_INTERVAL,
    NETWORK_NAME,
    OFFCHAIN_KEY,
    PROXY_ENDPOINTS,
)
from src.db import bootstrap_db
from src.logs import init_default_logger
from src.models import Address, TransactionCount, db

logger = logging.getLogger(__name__)


def run_migrations():
    logger.info('Running database migrations...')
    try:
        with db:
            db.create_tables([Address, TransactionCount])
        logger.info('Database migrations completed successfully.')
    except Exception as e:
        logger.error(f'Error running migrations: {e}')
        sys.exit(1)


def run_metrics_loop():
    if NETWORK_NAME not in PROXY_ENDPOINTS:
        logger.error(f'Unsupported network: {NETWORK_NAME}')
        sys.exit(1)

    logger.info(f'Starting metrics collection loop for network: {NETWORK_NAME}')
    last_run_date = None

    while True:
        current_date = datetime.now().date()

        if last_run_date is None or current_date > last_run_date:
            sleep(METRICS_CHECK_INTERVAL)
            logger.info(f'Daily metrics collection started for {NETWORK_NAME}...')
            try:
                with db.connection_context():
                    asyncio.run(collect_metrics(NETWORK_NAME))
                last_run_date = current_date
                logger.info(f'Daily metrics collection completed for {NETWORK_NAME}.')
                logger.info(f'Sleeping for {METRICS_CHECK_INTERVAL} seconds.')
                sleep(METRICS_CHECK_INTERVAL)
            except Exception as e:
                logger.exception(f'Error during metrics collection for {NETWORK_NAME}: {e}')
                logger.info(f'Sleeping for {METRICS_ERROR_CHECK_INTERVAL} seconds after error.')
                sleep(METRICS_ERROR_CHECK_INTERVAL)
        else:
            logger.info(
                f'Not time for collection yet. \
                Last run: {last_run_date}, Current date: {current_date}'
            )
            logger.info(f'Sleeping for {METRICS_CHECK_INTERVAL} seconds.')
            sleep(METRICS_CHECK_INTERVAL)


def wait_for_db():
    for _ in range(DB_CONNECTION_RETRIES):
        try:
            db.connect()
            db.close()
            logger.info('Successfully connected to the database.')
            return
        except Exception as e:
            logger.exception(e)
            logger.warning(
                f'Database connection failed. Retrying in {DB_CONNECTION_INTERVAL} seconds...'
            )
            sleep(DB_CONNECTION_INTERVAL)

    logger.error('Failed to connect to the database after multiple attempts.')
    sys.exit(1)


async def bootstrap_database():
    logger.info('Checking if database needs bootstrapping...')
    try:
        async with aiohttp.ClientSession() as session:
            metadata = await download_metadata(session, NETWORK_NAME)

            apps_data = {}
            for chain_name, chain_info in metadata.items():
                if chain_name != OFFCHAIN_KEY and 'apps' in chain_info:
                    apps_data[chain_name] = {
                        app_name: app_info.get('contracts', [])
                        for app_name, app_info in chain_info['apps'].items()
                    }

            await bootstrap_db(session, apps_data)
    except Exception as e:
        logger.exception(f'Error bootstrapping database: {e}')
        sys.exit(1)


if __name__ == '__main__':
    init_default_logger()
    logger.info(f'Starting metrics collector for network: {NETWORK_NAME}')
    wait_for_db()
    run_migrations()
    asyncio.run(bootstrap_database())
    run_metrics_loop()
