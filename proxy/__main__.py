import json
import logging
import os
import time
from pathlib import Path

import requests
from skale import SkaleManager

from proxy import nginx
from proxy.chains import (
    CHAINS_JSON,
    METADATA_URL,
    Chain,
    ChainRecord,
    Metadata,
    atomic_write,
    chain_record,
    discover,
    get_json,
    probe,
)

logger = logging.getLogger('proxy')

INTERVAL = 600
RETRY_INTERVAL = 30


def saved(path: Path) -> Metadata:
    records: list[ChainRecord] = json.loads(path.read_text()) if path.exists() else []
    return {r['schain']['name']: r['chain_metadata'] for r in records if r['chain_metadata']}


def heartbeat(session: requests.Session, url: str) -> None:
    try:
        session.get(url, timeout=10).raise_for_status()
    except requests.RequestException as e:
        logger.warning('Heartbeat failed: %s', type(e).__name__)


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    network, heartbeat_url = os.environ['NETWORK_NAME'], os.environ.get('HEARTBEAT_URL')
    endpoint, contracts = os.environ['ENDPOINT'], os.environ['MANAGER_CONTRACTS']
    session = requests.Session()
    skale: SkaleManager | None = None
    chains: list[Chain] = []
    metadata = saved(CHAINS_JSON)
    while True:
        try:
            skale = skale or SkaleManager(endpoint, contracts)
            chains, fresh = discover(skale), True
        except Exception:
            fresh = False
            logger.exception('Discovery failed, keeping the last known chains')
        metadata = get_json(session, METADATA_URL.format(network)) or metadata
        if chains:
            stamps = probe(session, chains)
            records = [chain_record(c, stamps, metadata) for c in chains]
            if nginx.apply(nginx.render(records)):
                atomic_write(CHAINS_JSON, json.dumps(records, separators=(',', ':')))
                if fresh and heartbeat_url and nginx.serving():
                    heartbeat(session, heartbeat_url)
        time.sleep(INTERVAL if fresh else RETRY_INTERVAL)


if __name__ == '__main__':
    main()
