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

from web3 import Web3, HTTPProvider
from Crypto.Hash import keccak

from proxy.skaled_ports import SkaledPorts
from proxy.helper import ip_from_bytes, read_json, write_json
from proxy.config import PORTS_PER_SCHAIN, ENDPOINT, SM_ABI_FILEPATH


URL_PREFIXES = {
    'http': 'http://',
    'https': 'https://',
    'ws': 'ws://',
    'wss': 'wss://',
    'infoHttp': 'http://'
}


def schain_name_to_id(name: str) -> str:
    keccak_hash = keccak.new(data=name.encode("utf8"), digest_bits=256)
    return '0x' + keccak_hash.hexdigest()


def schain_name_to_network_id(name: str) -> str:
    schain_name_to_id(name)


def get_schain_index_in_node(schain_id, schains_ids_on_node):
    for index, schain_id_on_node in enumerate(schains_ids_on_node):
        if schain_id == schain_id_on_node:
            return index
    raise Exception(f'sChain {schain_id} is not found in the list: {schains_ids_on_node}')


def get_schain_base_port_on_node(schain_id, schains_ids_on_node, node_base_port):
    schain_index = get_schain_index_in_node(schain_id, schains_ids_on_node)
    return calc_schain_base_port(node_base_port, schain_index)


def calc_schain_base_port(node_base_port, schain_index):
    return node_base_port + schain_index * PORTS_PER_SCHAIN


def calc_ports(schain_base_port):
    return {
        'httpRpcPort': schain_base_port + SkaledPorts.HTTP_JSON.value,
        'httpsRpcPort': schain_base_port + SkaledPorts.HTTPS_JSON.value,
        'wsRpcPort': schain_base_port + SkaledPorts.WS_JSON.value,
        'wssRpcPort': schain_base_port + SkaledPorts.WSS_JSON.value,
        'infoHttpRpcPort': schain_base_port + SkaledPorts.INFO_HTTP_JSON.value
    }


def _compose_endpoints(node_dict, endpoint_type):
    for prefix_name in URL_PREFIXES:
        prefix = URL_PREFIXES[prefix_name]
        port = node_dict[f'{prefix_name}RpcPort']
        key_name = f'{prefix_name}_endpoint_{endpoint_type}'
        node_dict[key_name] = f'{prefix}{node_dict[endpoint_type]}:{port}'


def endpoints_for_schain(schains_internal_contract, nodes_contract, schain_id):
    """Generates endpoints list for a given SKALE chain"""
    node_ids = schains_internal_contract.functions.getNodesInGroup(schain_id).call()
    nodes = []
    for node_id in node_ids:
        node = nodes_contract.functions.nodes(node_id).call()
        node_dict = {
            'id': node_id,
            'name': node[0],
            'ip': ip_from_bytes(node[1]),
            'base_port': node[3],
            'domain': nodes_contract.functions.getNodeDomainName(node_id).call()
        }
        schain_ids = schains_internal_contract.functions.getSchainIdsForNode(node_id).call()
        node_dict['schain_base_port'] = get_schain_base_port_on_node(
            schain_id, schain_ids, node_dict['base_port']
        )
        node_dict.update(calc_ports(node_dict['schain_base_port']))

        _compose_endpoints(node_dict, endpoint_type='ip')
        _compose_endpoints(node_dict, endpoint_type='domain')

        nodes.append(node_dict)

    schain = schains_internal_contract.functions.schains(schain_id).call()
    return {
        'schain': schain,
        'schain_id': schain_name_to_id(schain[0])[:15],
        'nodes': nodes
    }


def init_contracts(web3: Web3, sm_abi: str):
    schains_internal_contract = web3.eth.contract(
        address=sm_abi['schains_internal_address'],
        abi=sm_abi['schains_internal_abi']
    )
    nodes_contract = web3.eth.contract(
        address=sm_abi['nodes_address'],
        abi=sm_abi['nodes_abi']
    )
    return schains_internal_contract, nodes_contract


def endpoints_for_all_schains(endpoint: str, abi_filepath: str) -> list:
    """Main function that generates endpoints for all SKALE Chains on the given network"""
    provider = HTTPProvider(endpoint)
    web3 = Web3(provider)
    sm_abi = read_json(abi_filepath)

    schains_internal_contract, nodes_contract = init_contracts(
        web3=web3,
        sm_abi=sm_abi
    )

    schain_ids = schains_internal_contract.functions.getSchains().call()

    schain_ids = [schain_ids[0]] # TODO: TMP!

    endpoints = [
        endpoints_for_schain(schains_internal_contract, nodes_contract, schain_id)
        for schain_id in schain_ids
    ]
    return endpoints


if __name__ == '__main__':
    endpoints = endpoints_for_all_schains(ENDPOINT, SM_ABI_FILEPATH)
    print(json.dumps(endpoints, indent=4))
    # write_json(RESULTS_PATH, endpoints)
