import json
import logging
import os
import time
from pathlib import Path

import requests
from skale import SkaleManager
from skale.types.schain import SchainHash

from proxy import nginx
from proxy.chains import (
    CHAINS_JSON,
    Chain,
    ChainRecord,
    Metadata,
    atomic_write,
    chain_record,
    discover,
    fetch_metadata,
    probe,
)

logger = logging.getLogger('proxy')

INTERVAL = 600


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
    session = requests.Session()
    skale = SkaleManager(os.environ['ENDPOINT'], os.environ['MANAGER_CONTRACTS'])
    chains: dict[SchainHash, Chain] = {}
    metadata = saved(CHAINS_JSON)
    while True:
        try:
            chains, fresh = discover(skale), True
        except Exception:
            fresh = False
            logger.exception('Discovery failed, keeping the last known chains')
        metadata = fetch_metadata(session, network) or metadata
        if chains:
            stamps = probe(session, chains)
            records = [chain_record(c, stamps, metadata) for c in chains.values()]
            if nginx.apply(nginx.render(records)):
                atomic_write(CHAINS_JSON, json.dumps(records, separators=(',', ':')))
                if fresh and heartbeat_url:
                    heartbeat(session, heartbeat_url)
        time.sleep(INTERVAL)


if __name__ == '__main__':
    main()
