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

import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from time import sleep

import requests
from Crypto.Hash import keccak
from skale import SkaleManager
from skale.dataclasses.node_info import NodeInfo
from skale.schain_config.ports_allocation import get_schain_base_port_on_node
from skale.types.node import NodeId
from skale.types.schain import SchainHash, SchainName
from skale.utils.helper import ip_from_bytes

from proxy.config import ALLOWED_TIMESTAMP_DIFF, GITHUB_RAW_URL, get_config
from proxy.helper import init_default_logger, make_rpc_call
from proxy.str_formatters import arguments_list_string

logger = logging.getLogger(__name__)


URL_PREFIXES = {
    'http': 'http://',
    'https': 'https://',
    'ws': 'ws://',
    'wss': 'wss://',
}


class ChainsMetadataDownloadError(Exception):
    """Raised when chains metadata cannot be downloaded."""


class ChainInfo:
    def __init__(self, schain_name: SchainName, nodes: list):
        self.schain_name = schain_name
        self.chain_id = schain_name_to_network_id(schain_name)
        self.http_endpoints = []
        self.ws_endpoints = []
        self.fs_endpoints = []
        self._format_nodes(nodes)

    def _format_nodes(self, nodes):
        for node in nodes:
            http_endpoint = node['http_endpoint_domain']
            node['block_ts'] = get_block_ts(http_endpoint)

        max_ts = max(node['block_ts'] for node in nodes)
        logger.info(f'max_ts: {max_ts}')

        for node in nodes:
            http_endpoint = node['http_endpoint_domain']
            if not url_ok(http_endpoint):
                logger.warning(f'{http_endpoint} is not accessible, removing from the list')
                continue
            if is_node_out_of_sync(node['block_ts'], max_ts):
                logger.warning(
                    f'{http_endpoint} ts: {node["block_ts"]}, max ts for chain: \
{max_ts}, allowed timestamp diff: {ALLOWED_TIMESTAMP_DIFF}'
                )
                continue
            self.http_endpoints.append(http_endpoint.removeprefix(URL_PREFIXES['http']))
            self.ws_endpoints.append(node['ws_endpoint_domain'].removeprefix(URL_PREFIXES['ws']))
            self.fs_endpoints.append(node['domain'])

    def to_dict(self):
        return {
            'schain_name': self.schain_name,
            'chain_id': self.chain_id,
            'http_endpoints': self.http_endpoints,
            'ws_endpoints': self.ws_endpoints,
            'fs_endpoints': self.fs_endpoints,
        }


def download_metadata(network_name: str) -> dict | None:
    """Download and parse network metadata."""
    url = f'{GITHUB_RAW_URL}/skalenetwork/skale-network/master/metadata/{network_name}/chains.json'
    max_retries = 5
    for attempt in range(max_retries):
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            if attempt < max_retries - 1:
                logger.warning(
                    f'Failed to download metadata from {url} '
                    f'(attempt {attempt + 1}/{max_retries}): {e}'
                )
                sleep(2)
            else:
                raise ChainsMetadataDownloadError(e)

    return None


def url_ok(url) -> bool:
    try:
        r = requests.head(url, timeout=10)
        return bool(r.status_code)
    except requests.exceptions.RequestException:
        return False


def is_node_out_of_sync(ts: int, compare_ts: int) -> bool:
    return abs(compare_ts - ts) > ALLOWED_TIMESTAMP_DIFF


def get_block_ts(http_endpoint: str) -> int:
    try:
        res = make_rpc_call(http_endpoint, 'eth_getBlockByNumber', ['latest', False])
        if res and res.json():
            res_data = res.json()
            latest_schain_timestamp_hex = res_data['result']['timestamp']
            return int(latest_schain_timestamp_hex, 16)
    except Exception as e:
        logger.warning(f'Failed to request latest block for {http_endpoint} ({e})')
    return -1


def schain_name_to_id(name: str) -> str:
    keccak_hash = keccak.new(data=name.encode('utf8'), digest_bits=256)
    return '0x' + keccak_hash.hexdigest()


def schain_name_to_network_id(schain_name: SchainName) -> str:
    return schain_name_to_id(schain_name)[:15]


def _compose_endpoints(node_dict: dict, endpoint_type: str):
    for prefix_name in URL_PREFIXES:
        prefix = URL_PREFIXES[prefix_name]
        port = node_dict[f'{prefix_name}RpcPort']
        key_name = f'{prefix_name}_endpoint_{endpoint_type}'
        node_dict[key_name] = f'{prefix}{node_dict[endpoint_type]}:{port}'


def get_node_info(
    skale: SkaleManager,
    schain_hash: SchainHash,
    node_id: NodeId,
) -> dict:
    node = skale.nodes.get(node_id)
    schain_hashes = skale.schains_internal.get_schain_hashes_for_node(node_id)
    base_port = get_schain_base_port_on_node(schain_hashes, schain_hash, node['port'])
    node_dict = NodeInfo(node_id=node_id, name=node['name'], base_port=base_port).to_dict()
    node_dict['ip'] = ip_from_bytes(node['ip'])
    node_dict['domain'] = node['domain_name']
    return node_dict


def generate_endpoints_for_schain(
    skale: SkaleManager, schain_hash: SchainHash, chains_metadata: dict | None
):
    schain = skale.schains.get(schain_hash)
    logger.info(f'Going to generate endpoints for sChain: {schain.name}')

    node_ids = skale.schains_internal.get_node_ids_for_schain(schain.name)
    nodes = []
    for node_id in node_ids:
        node = get_node_info(
            skale=skale,
            schain_hash=schain_hash,
            node_id=node_id,
        )
        _compose_endpoints(node, endpoint_type='ip')
        _compose_endpoints(node, endpoint_type='domain')
        nodes.append(node)

    chain_metadata = None
    if chains_metadata and schain.name in chains_metadata:
        chain_metadata = chains_metadata[schain.name]
        if 'apps' in chain_metadata:
            chain_metadata.pop('apps')
    return {
        'schain': schain.to_dict(),
        'nodes': nodes,
        'chain_info': ChainInfo(schain.name, nodes).to_dict(),
        'chain_metadata': chain_metadata,
    }


def generate_endpoints(endpoint: str, manager_contracts: str, network_name: str) -> list:
    """Main function that generates endpoints for all SKALE Chains on the given network"""

    chains_metadata = download_metadata(network_name=network_name)
    skale = SkaleManager(endpoint, manager_contracts)

    logger.info(
        arguments_list_string(
            {
                'nodes': skale.nodes.address,
                'schains_internal': skale.schains_internal.address,
                'schains': skale.schains.address,
            },
            'Contracts inited',
        )
    )

    schain_hashes = skale.schains_internal.get_all_schains_hashes()

    logger.info(f'Number of sChains: {len(schain_hashes)}')
    endpoints = []

    with ThreadPoolExecutor() as executor:
        future_to_schain_hash = {
            executor.submit(
                generate_endpoints_for_schain,
                skale,
                schain_hash,
                chains_metadata,
            ): schain_hash
            for schain_hash in schain_hashes
        }
        for future in as_completed(future_to_schain_hash):
            schain_hash = future_to_schain_hash[future]
            try:
                result = future.result()
                if result is not None:
                    endpoints.append(result)
            except Exception as e:
                logger.error(f'Failed to generate endpoints for sChain {schain_hash}: {e}')

    return endpoints


if __name__ == '__main__':
    init_default_logger()
    config = get_config()
    schains_endpoints = generate_endpoints(
        config.endpoint, config.manager_contracts, config.network_name
    )
    print(json.dumps(schains_endpoints, indent=4))
