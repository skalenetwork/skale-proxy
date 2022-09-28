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

from web3.contract import Contract

from proxy.skaled_ports import SkaledPorts
from proxy.config import PORTS_PER_SCHAIN
from proxy.helper import ip_from_bytes


def get_node_info(
    schain_hash: str,
    node_id: int,
    nodes_contract: Contract,
    schains_internal_contract: Contract
) -> dict:
    node = nodes_contract.functions.nodes(node_id).call()
    node_dict = {
        'id': node_id,
        'name': node[0],
        'ip': ip_from_bytes(node[1]),
        'base_port': node[3],
        'domain': nodes_contract.functions.getNodeDomainName(node_id).call()
    }
    schain_hashes = schains_internal_contract.functions.getSchainHashesForNode(node_id).call()
    node_dict['schain_base_port'] = _get_schain_base_port_on_node(
        schain_hash, schain_hashes, node_dict['base_port']
    )
    node_dict.update(_calc_ports(node_dict['schain_base_port']))
    return node_dict


def _get_schain_index_in_node(schain_hash, schains_hashes_on_node):
    for index, schain_hash_on_node in enumerate(schains_hashes_on_node):
        if schain_hash == schain_hash_on_node:
            return index
    raise Exception(f'sChain {schain_hash} is not found in the list: {schains_hashes_on_node}')


def _get_schain_base_port_on_node(schain_hash, schains_hashes_on_node, node_base_port):
    schain_index = _get_schain_index_in_node(schain_hash, schains_hashes_on_node)
    return _calc_schain_base_port(node_base_port, schain_index)


def _calc_schain_base_port(node_base_port, schain_index):
    return node_base_port + schain_index * PORTS_PER_SCHAIN


def _calc_ports(schain_base_port):
    return {
        'httpRpcPort': schain_base_port + SkaledPorts.HTTP_JSON.value,
        'httpsRpcPort': schain_base_port + SkaledPorts.HTTPS_JSON.value,
        'wsRpcPort': schain_base_port + SkaledPorts.WS_JSON.value,
        'wssRpcPort': schain_base_port + SkaledPorts.WSS_JSON.value,
        'infoHttpRpcPort': schain_base_port + SkaledPorts.INFO_HTTP_JSON.value
    }
