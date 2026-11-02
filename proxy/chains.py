import logging
import os
from collections.abc import Mapping
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from functools import partial
from pathlib import Path
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

    @property
    def ids(self) -> frozenset[NodeId]:
        return frozenset(n.id for n in self.nodes)


@dataclass(frozen=True, slots=True)
class NodeData:
    name: str
    ip: str
    domain: str
    port: Port
    hashes: list[SchainHash]


class NodeRecord(TypedDict):
    nodeID: NodeId
    nodeName: str
    basePort: Port
    httpRpcPort: Port
    httpsRpcPort: Port
    wsRpcPort: Port
    wssRpcPort: Port
    ip: str
    domain: str
    http_endpoint_ip: str
    https_endpoint_ip: str
    ws_endpoint_ip: str
    wss_endpoint_ip: str
    http_endpoint_domain: str
    https_endpoint_domain: str
    ws_endpoint_domain: str
    wss_endpoint_domain: str
    block_ts: int


class ChainInfo(TypedDict):
    schain_name: str
    chain_id: str
    http_endpoints: list[str]
    ws_endpoints: list[str]
    fs_endpoints: list[str]


class ChainRecord(TypedDict):
    schain: dict[str, Any]
    nodes: list[NodeRecord]
    chain_info: ChainInfo
    chain_metadata: dict[str, Any] | None


def atomic_write(path: Path, text: str) -> None:
    tmp = path.with_name(f'{path.name}.tmp')
    tmp.write_text(text)
    os.replace(tmp, path)


def node_data(skale: SkaleManager, node_id: NodeId) -> NodeData:
    node = skale.nodes.get(node_id)
    hashes = skale.schains_internal.schain_hashes_for_node(node_id)
    return NodeData(
        node['name'], ip_from_bytes(node['ip']), node['domain_name'], node['port'], hashes
    )


def build(
    schain_hash: SchainHash,
    schain: SchainStructure,
    group: list[NodeId],
    data: Mapping[NodeId, NodeData],
) -> Chain:
    nodes = tuple(
        Node(i, d.name, d.ip, d.domain, get_schain_base_port_on_node(d.hashes, schain_hash, d.port))
        for i in group
        if (d := data[i])
    )
    return Chain(schain.name, schain.to_dict(), nodes)


def discover(skale: SkaleManager) -> dict[SchainHash, Chain]:
    hashes = skale.schains_internal.all_schain_hashes()
    with ThreadPoolExecutor(8) as pool:
        schains = list(pool.map(skale.schains.get, hashes))
        groups = list(pool.map(skale.schains_internal.node_ids_for_schain_hash, hashes))
        ids = list({i for group in groups for i in group})
        data = dict(zip(ids, pool.map(partial(node_data, skale), ids), strict=True))
    return {h: build(h, s, g, data) for h, s, g in zip(hashes, schains, groups, strict=True)}


def fetch_metadata(session: requests.Session, network: str) -> Metadata | None:
    try:
        response = session.get(METADATA_URL.format(network), timeout=10)
        response.raise_for_status()
        metadata: Metadata = response.json()
        return metadata
    except requests.RequestException:
        logger.warning('Metadata download failed, keeping the last good copy')
        return None


def block_field(session: requests.Session, url: str, field: str) -> int | None:
    try:
        response = session.post(
            url,
            json={
                'jsonrpc': '2.0',
                'id': 1,
                'method': 'eth_getBlockByNumber',
                'params': ['latest', False],
            },
            timeout=(3, 5),
        )
        response.raise_for_status()
        return int(response.json()['result'][field], 16)
    except requests.RequestException, ValueError, LookupError, TypeError:
        return None


def probe(session: requests.Session, chains: Mapping[SchainHash, Chain]) -> dict[Node, int]:
    nodes = [n for c in chains.values() for n in c.nodes]
    with ThreadPoolExecutor(32) as pool:
        stamps = pool.map(lambda n: block_field(session, n.rpc_url, 'timestamp'), nodes)
    return {n: -1 if ts is None else ts for n, ts in zip(nodes, stamps, strict=True)}


def healthy(chain: Chain, stamps: Mapping[Node, int]) -> frozenset[NodeId]:
    ts = {n.id: stamps[n] for n in chain.nodes}
    newest = max((t for t in ts.values() if t > 0), default=0)
    return frozenset(i for i, t in ts.items() if t > 0 and newest - t <= MAX_LAG)


def node_record(node: Node, ts: int) -> NodeRecord:
    p = node.ports
    return {
        'nodeID': node.id,
        'nodeName': node.name,
        'basePort': node.base_port,
        'httpRpcPort': p['httpRpcPort'],
        'httpsRpcPort': p['httpsRpcPort'],
        'wsRpcPort': p['wsRpcPort'],
        'wssRpcPort': p['wssRpcPort'],
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
    routed = healthy(chain, stamps) or chain.ids
    nodes = [n for n in chain.nodes if n.id in routed]
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
