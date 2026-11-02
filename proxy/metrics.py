import json
import logging
import os
import sqlite3
import time
from collections.abc import Iterable, Mapping
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any, TypedDict

import requests

from proxy.chains import CHAINS_JSON, Metadata, atomic_write, block_field, fetch_metadata

logger = logging.getLogger('metrics')

STATE = Path('/var/lib/metrics')
CHECK_INTERVAL = 600
EXPLORERS = {
    'mainnet': 'explorer.mainnet.skalenodes.com',
    'testnet': 'explorer.testnet.skalenodes.com',
    'legacy': 'legacy-explorer.skalenodes.com',
    'regression': 'regression-explorer.skalenodes.com',
}
COUNTER_FIELDS = (
    'gas_usage_count',
    'token_transfers_count',
    'transactions_count',
    'validations_count',
)
SCHEMA = """CREATE TABLE IF NOT EXISTS counters (
    chain TEXT NOT NULL, address TEXT NOT NULL, day TEXT NOT NULL, counters TEXT NOT NULL,
    PRIMARY KEY (chain, address, day)) WITHOUT ROWID"""

type Counters = dict[str, str]


class AddressCounter(TypedDict):
    gas_usage_count: str
    token_transfers_count: str
    transactions_count: str
    validations_count: str
    transactions_today: int
    transactions_last_7_days: int
    transactions_last_30_days: int


class ChainMetrics(TypedDict):
    apps_counters: dict[str, dict[str, AddressCounter]]
    chain_stats: dict[str, Any]


class MetricsFile(TypedDict):
    metrics: dict[str, ChainMetrics]
    gas: int
    last_updated: int


def apps(meta: Mapping[str, Any]) -> dict[str, list[str]]:
    return {
        name: app['contracts'] for name, app in meta.get('apps', {}).items() if 'contracts' in app
    }


def counters(session: requests.Session, url: str, address: str) -> Counters | None:
    try:
        response = session.get(f'{url}/api/v2/addresses/{address}/counters', timeout=10)
        if response.status_code == 404:
            return dict.fromkeys(COUNTER_FIELDS, '0')
        response.raise_for_status()
        data = response.json()
        return {f: str(data.get(f, '0')) for f in COUNTER_FIELDS}
    except requests.RequestException:
        logger.warning('Counters failed for %s on %s', address, url)
        return None


def chain_stats(session: requests.Session, url: str) -> dict[str, Any] | None:
    try:
        response = session.get(f'{url}/api/v2/stats', timeout=10)
        response.raise_for_status()
        stats: dict[str, Any] = response.json()
        return stats
    except requests.RequestException:
        logger.warning('Stats failed for %s', url)
        return None


def window(history: Mapping[date, int], days: int) -> int:
    latest = max(history)
    past = [d for d in history if d <= latest - timedelta(days=days)]
    base = history[max(past)] if past else history[min(history)]
    return max(0, history[latest] - base)


def counter(history: Mapping[date, Counters]) -> AddressCounter:
    totals = {d: int(c['transactions_count']) for d, c in history.items()}
    latest = history[max(history)]
    return {
        'gas_usage_count': latest['gas_usage_count'],
        'token_transfers_count': latest['token_transfers_count'],
        'transactions_count': latest['transactions_count'],
        'validations_count': latest['validations_count'],
        'transactions_today': window(totals, 1),
        'transactions_last_7_days': window(totals, 7),
        'transactions_last_30_days': window(totals, 30),
    }


def history(db: sqlite3.Connection, today: date) -> dict[tuple[str, str], dict[date, Counters]]:
    rows = db.execute(
        'SELECT chain, address, day, counters FROM counters WHERE day >= ?',
        [str(today - timedelta(days=31))],
    )
    result: dict[tuple[str, str], dict[date, Counters]] = {}
    for chain, address, day, data in rows:
        result.setdefault((chain, address), {})[date.fromisoformat(day)] = json.loads(data)
    return result


def collect(
    session: requests.Session,
    db: sqlite3.Connection,
    network: str,
    chains: Iterable[str],
    metadata: Metadata,
    previous: MetricsFile | None,
    endpoint: str,
) -> MetricsFile | None:
    today = datetime.now(UTC).date()
    urls = {c: f'https://{c}.{EXPLORERS[network]}' for c in chains if c in metadata}
    pairs = {(c, a) for c in urls for addresses in apps(metadata[c]).values() for a in addresses}
    known = history(db, today)
    missing = [p for p in pairs if today not in known.get(p, {})]
    if (
        not missing
        and previous
        and datetime.fromtimestamp(previous['last_updated'], UTC).date() == today
    ):
        return None
    with ThreadPoolExecutor(8) as pool:
        fetched = list(pool.map(lambda p: counters(session, urls[p[0]], p[1]), missing))
        stats = dict(
            zip(urls, pool.map(lambda u: chain_stats(session, u), urls.values()), strict=True)
        )
    with db:
        db.executemany(
            'INSERT OR REPLACE INTO counters VALUES (?, ?, ?, ?)',
            [
                (c, a, str(today), json.dumps(f))
                for (c, a), f in zip(missing, fetched, strict=True)
                if f
            ],
        )
    known = history(db, today)
    old = {c: m['chain_stats'] for c, m in previous['metrics'].items()} if previous else {}
    fee = block_field(session, endpoint, 'baseFeePerGas')
    return {
        'metrics': {
            chain: {
                'chain_stats': s,
                'apps_counters': {
                    app: {a: counter(known[chain, a]) for a in addresses if (chain, a) in known}
                    for app, addresses in apps(metadata[chain]).items()
                },
            }
            for chain in urls
            if (s := stats[chain] or old.get(chain))
        },
        'gas': fee if fee is not None else previous['gas'] if previous else 0,
        'last_updated': int(time.time()),
    }


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    network, endpoint = os.environ['NETWORK_NAME'], os.environ['ETH_ENDPOINT']
    output = STATE / 'metrics.json'
    session = requests.Session()
    db = sqlite3.connect(STATE / 'metrics.db')
    db.execute(SCHEMA)
    while True:
        metadata = fetch_metadata(session, network)
        if metadata is not None and CHAINS_JSON.exists():
            chains = [c['schain']['name'] for c in json.loads(CHAINS_JSON.read_text())]
            previous: MetricsFile | None = (
                json.loads(output.read_text()) if output.exists() else None
            )
            if data := collect(session, db, network, chains, metadata, previous, endpoint):
                atomic_write(output, json.dumps(data, separators=(',', ':')))
                logger.info('metrics.json written for %d chains', len(data['metrics']))
        time.sleep(CHECK_INTERVAL)


if __name__ == '__main__':
    main()
