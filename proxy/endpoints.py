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

import requests

from web3 import Web3, HTTPProvider
from Crypto.Hash import keccak

from proxy.node_info import get_node_info
from proxy.helper import read_json, make_rpc_call
from proxy.config import ENDPOINT, SM_ABI_FILEPATH
from proxy.str_formatters import arguments_list_string
from proxy.schain_options import parse_schain_options
from proxy.config import ALLOWED_TIMESTAMP_DIFF

logger = logging.getLogger(__name__)


URL_PREFIXES = {
    'http': 'http://',
    'https': 'https://',
    'ws': 'ws://',
    'wss': 'wss://',
    'infoHttp': 'http://'
}


class ChainInfo:
    def __init__(self, schain_name: str, nodes: list):
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
                logger.warning(f'{http_endpoint} is not accesible, removing from the list')
                continue
            if is_node_out_of_sync(node['block_ts'], max_ts):
                logger.warning(f'{http_endpoint} ts: {node["block_ts"]}, max ts for chain: \
{max_ts}, allowed timestamp diff: {ALLOWED_TIMESTAMP_DIFF}')
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
            'fs_endpoints': self.fs_endpoints
        }


def url_ok(url) -> bool:
    try:
        r = requests.head(url)
        return bool(r.status_code)
    except requests.exceptions.ConnectionError:
        return False


def is_node_out_of_sync(ts: int, compare_ts: int) -> bool:
    return abs(compare_ts - ts) > ALLOWED_TIMESTAMP_DIFF


def get_block_ts(http_endpoint: str) -> int:
    res = make_rpc_call(http_endpoint, 'eth_getBlockByNumber', ['latest', False])
    if res and res.json():
        res_data = res.json()
        latest_schain_timestamp_hex = res_data['result']['timestamp']
        return int(latest_schain_timestamp_hex, 16)
    return -1


def schain_name_to_id(name: str) -> str:
    keccak_hash = keccak.new(data=name.encode("utf8"), digest_bits=256)
    return '0x' + keccak_hash.hexdigest()


def schain_name_to_network_id(raw_schain_struct: list) -> str:
    return schain_name_to_id(raw_schain_struct[0])[:15]


def _compose_endpoints(node_dict, endpoint_type):
    for prefix_name in URL_PREFIXES:
        prefix = URL_PREFIXES[prefix_name]
        port = node_dict[f'{prefix_name}RpcPort']
        key_name = f'{prefix_name}_endpoint_{endpoint_type}'
        node_dict[key_name] = f'{prefix}{node_dict[endpoint_type]}:{port}'


def generate_endpoints_for_schain(
    schains_internal_contract,
    schains_contract,
    nodes_contract,
    schain_hash
):
    """Generates endpoints list for a given SKALE chain"""
    schain = schains_internal_contract.functions.schains(schain_hash).call()
    schain_options_raw = schains_contract.functions.getOptions(schain_hash).call()

    schain_options = parse_schain_options(
        raw_options=schain_options_raw
    )

    schain.append(schain_options.multitransaction_mode)
    schain.append(schain_options.threshold_encryption)

    logger.info(f'Going to generate endpoints for sChain: {schain[0]}')

    node_ids = schains_internal_contract.functions.getNodesInGroup(schain_hash).call()
    nodes = []
    for node_id in node_ids:
        node = get_node_info(
            schain_hash=schain_hash,
            node_id=node_id,
            nodes_contract=nodes_contract,
            schains_internal_contract=schains_internal_contract
        )
        _compose_endpoints(node, endpoint_type='ip')
        _compose_endpoints(node, endpoint_type='domain')
        nodes.append(node)
    return {
        'schain': schain,
        'nodes': nodes,
        'chain_info': ChainInfo(schain[0], nodes).to_dict()
    }


def init_contracts(web3: Web3, sm_abi: str):
    schains_internal_contract = web3.eth.contract(
        address=sm_abi['schains_internal_address'],
        abi=sm_abi['schains_internal_abi']
    )
    schains_contract = web3.eth.contract(
        address=sm_abi['schains_address'],
        abi=sm_abi['schains_abi']
    )
    nodes_contract = web3.eth.contract(
        address=sm_abi['nodes_address'],
        abi=sm_abi['nodes_abi']
    )
    return schains_internal_contract, schains_contract, nodes_contract


def generate_endpoints(endpoint: str, abi_filepath: str) -> list:
    """Main function that generates endpoints for all SKALE Chains on the given network"""
    provider = HTTPProvider(endpoint)
    web3 = Web3(provider)
    sm_abi = read_json(abi_filepath)

    schains_internal_contract, schains_contract, nodes_contract = init_contracts(
        web3=web3,
        sm_abi=sm_abi
    )

    logger.info(arguments_list_string({
        'nodes': nodes_contract.address,
        'schains_internal': schains_internal_contract.address,
        'schains': schains_contract.address
        }, 'Contracts inited'))

    schain_hashes = schains_internal_contract.functions.getSchains().call()

    logger.info(f'Number of sChains: {len(schain_hashes)}')
    endpoints = [
        generate_endpoints_for_schain(
            schains_internal_contract, schains_contract, nodes_contract, schain_hash)
        for schain_hash in schain_hashes
    ]
    endpoints = list(filter(lambda item: item is not None, endpoints))  # TODO: hotfix!
    return endpoints


if __name__ == '__main__':
    schains_endpoints = generate_endpoints(ENDPOINT, SM_ABI_FILEPATH)
    print(json.dumps(schains_endpoints, indent=4))
