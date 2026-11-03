import json
import logging
import re
from collections.abc import Iterable, Mapping
from concurrent.futures import ThreadPoolExecutor, wait
from contextlib import suppress
from dataclasses import dataclass
from functools import partial
from pathlib import Path
from statistics import median_low
from typing import Any, TypedDict

import requests
from skale import SkaleManager
from skale.dataclasses.node_info import NodeInfo
from skale.schain_config.ports_allocation import get_schain_base_port_on_node
from skale.types.node import NodeId, Port
from skale.types.schain import SchainHash, SchainStructure
from skale.utils.helper import ip_from_bytes

logger = logging.getLogger(__name__)

type Metadata = dict[str, dict[str, Any]]

CHAINS_JSON = Path('/app/www/chains.json')
METADATA_URL = (
    'https://raw.githubusercontent.com/skalenetwork/skale-network/master/metadata/{}/chains.json'
)
MAX_LAG = 300
MAX_BODY = 1 << 21
PROBE_TIMEOUT = 60
DOMAIN = re.compile(r'[A-Za-z0-9._-]{1,253}')


@dataclass(frozen=True, slots=True)
class Node:
    id: NodeId
    name: str
    ip: str
    domain: str
    base_port: Port

    @property
    def ports(self) -> dict[str, Port]:
        return NodeInfo(self.id, self.name, self.base_port).calc_ports()

    @property
    def rpc_url(self) -> str:
        return f'http://{self.domain}:{self.ports["httpRpcPort"]}'


@dataclass(frozen=True, slots=True)
class Chain:
    name: str
    schain: dict[str, Any]
    nodes: tuple[Node, ...]


@dataclass(frozen=True, slots=True)
class NodeData:
    name: str
    ip: str
    domain: str
    port: Port
    hashes: list[SchainHash]


class ChainInfo(TypedDict):
    schain_name: str
    chain_id: str
    http_endpoints: list[str]
    ws_endpoints: list[str]
    fs_endpoints: list[str]


class ChainRecord(TypedDict):
    schain: dict[str, Any]
    nodes: list[dict[str, Any]]
    chain_info: ChainInfo
    chain_metadata: dict[str, Any] | None


def atomic_write(path: Path, text: str) -> None:
    tmp = path.with_name(f'{path.name}.tmp')
    tmp.write_text(text)
    tmp.replace(path)


def get_schain(skale: SkaleManager, schain_hash: SchainHash) -> SchainStructure | None:
    with suppress(UnicodeDecodeError):
        return skale.schains.get(schain_hash)
    logger.warning('Skipping chain %s with a non-UTF-8 name', schain_hash.hex())
    return None


def node_data(skale: SkaleManager, node_id: NodeId) -> NodeData | None:
    with suppress(UnicodeDecodeError):
        node = skale.nodes.get(node_id)
        if DOMAIN.fullmatch(node['domain_name']):
            hashes = skale.schains_internal.schain_hashes_for_node(node_id)
            return NodeData(
                node['name'], ip_from_bytes(node['ip']), node['domain_name'], node['port'], hashes
            )
    logger.warning('Skipping node %d with an invalid domain', node_id)
    return None


def build(
    schain_hash: SchainHash,
    schain: SchainStructure,
    group: list[NodeId],
    data: Mapping[NodeId, NodeData | None],
) -> Chain:
    nodes = tuple(
        Node(i, d.name, d.ip, d.domain, get_schain_base_port_on_node(d.hashes, schain_hash, d.port))
        for i in group
        if (d := data[i])
    )
    return Chain(schain.name, schain.to_dict(), nodes)


def discover(skale: SkaleManager) -> list[Chain]:
    hashes = skale.schains_internal.all_schain_hashes()
    with ThreadPoolExecutor(8) as pool:
        schains = list(pool.map(partial(get_schain, skale), hashes))
        groups = list(pool.map(skale.schains_internal.node_ids_for_schain_hash, hashes))
        ids = list({i for group in groups for i in group})
        data = dict(zip(ids, pool.map(partial(node_data, skale), ids), strict=True))
    return [build(h, s, g, data) for h, s, g in zip(hashes, schains, groups, strict=True) if s]


def get_json(session: requests.Session, url: str) -> Any:
    try:
        response = session.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
        logger.warning('GET %s failed', url)
        return None


def block_field(session: requests.Session, url: str, field: str) -> int | None:
    try:
        with session.post(
            url,
            json={
                'jsonrpc': '2.0',
                'id': 1,
                'method': 'eth_getBlockByNumber',
                'params': ['latest', False],
            },
            timeout=(3, 5),
            stream=True,
        ) as response:
            response.raise_for_status()
            body = b''
            for chunk in response.iter_content(1 << 16):
                if len(body := body + chunk) > MAX_BODY:
                    return None
        value = int(json.loads(body)['result'][field], 16)
        return value if value < 1 << 64 else None
    except requests.RequestException, ValueError, LookupError, TypeError, RecursionError:
        return None


def probe(session: requests.Session, chains: Iterable[Chain]) -> dict[Node, int]:
    nodes = [n for c in chains for n in c.nodes]
    pool = ThreadPoolExecutor(32)
    futures = [pool.submit(block_field, session, n.rpc_url, 'timestamp') for n in nodes]
    done, _ = wait(futures, PROBE_TIMEOUT)
    pool.shutdown(wait=False, cancel_futures=True)
    stamps = [f.result() if f in done else None for f in futures]
    return {n: -1 if ts is None else ts for n, ts in zip(nodes, stamps, strict=True)}


def healthy(chain: Chain, stamps: Mapping[Node, int]) -> list[Node]:
    head = median_low([stamps[n] for n in chain.nodes if stamps[n] > 0] or [0])
    return [n for n in chain.nodes if stamps[n] > 0 and head - stamps[n] <= MAX_LAG]


def node_record(node: Node, ts: int) -> dict[str, Any]:
    p = node.ports
    return {
        'nodeID': node.id,
        'nodeName': node.name,
        'basePort': node.base_port,
        **p,
        'ip': node.ip,
        'domain': node.domain,
        'http_endpoint_ip': f'http://{node.ip}:{p["httpRpcPort"]}',
        'https_endpoint_ip': f'https://{node.ip}:{p["httpsRpcPort"]}',
        'ws_endpoint_ip': f'ws://{node.ip}:{p["wsRpcPort"]}',
        'wss_endpoint_ip': f'wss://{node.ip}:{p["wssRpcPort"]}',
        'http_endpoint_domain': f'http://{node.domain}:{p["httpRpcPort"]}',
        'https_endpoint_domain': f'https://{node.domain}:{p["httpsRpcPort"]}',
        'ws_endpoint_domain': f'ws://{node.domain}:{p["wsRpcPort"]}',
        'wss_endpoint_domain': f'wss://{node.domain}:{p["wssRpcPort"]}',
        'block_ts': ts,
    }


def chain_record(chain: Chain, stamps: Mapping[Node, int], metadata: Metadata) -> ChainRecord:
    nodes = healthy(chain, stamps) or chain.nodes
    meta = metadata.get(chain.name)
    return {
        'schain': chain.schain,
        'nodes': [node_record(n, stamps[n]) for n in chain.nodes],
        'chain_info': {
            'schain_name': chain.name,
            'chain_id': '0x' + chain.schain['schain_hash'][:13],
            'http_endpoints': [f'{n.domain}:{n.ports["httpRpcPort"]}' for n in nodes],
            'ws_endpoints': [f'{n.domain}:{n.ports["wsRpcPort"]}' for n in nodes],
            'fs_endpoints': [n.domain for n in nodes],
        },
        'chain_metadata': None if meta is None else {k: v for k, v in meta.items() if k != 'apps'},
    }
