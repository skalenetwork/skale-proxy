import json
from pathlib import Path

import pytest
from skale.types.node import NodeId, Port

from proxy import nginx
from proxy.__main__ import saved
from proxy.chains import MAX_LAG, Chain, Node, chain_record, healthy

GOLDEN = Path(__file__).parent / 'golden'
NODES = (
    Node(NodeId(1), 'a', '10.0.0.1', '127.0.0.1', Port(10000)),
    Node(NodeId(2), 'b', '10.0.0.2', '127.0.0.2', Port(10128)),
)
CHAIN = Chain(
    'elated-tan-skat', {'name': 'elated-tan-skat', 'schain_hash': '0000079f99296b6e'}, NODES
)
EMPTY = Chain('lonely-chain', {'name': 'lonely-chain', 'schain_hash': 'ab'}, ())
STAMPS = {NODES[0]: 100, NODES[1]: -1}
METADATA = {'elated-tan-skat': {'shortAlias': 'europa', 'apps': {}}}
RECORDS = [chain_record(CHAIN, STAMPS, METADATA), chain_record(EMPTY, {}, {})]


def test_render_matches_golden() -> None:
    files = nginx.render(RECORDS)
    assert {p.name: t for p, t in files.items()} == {
        p.name: p.read_text() for p in GOLDEN.glob('*.conf')
    }


def test_chain_id() -> None:
    assert RECORDS[0]['chain_info']['chain_id'] == '0x0000079f99296'


def test_saved_roundtrip(tmp_path: Path) -> None:
    path = tmp_path / 'chains.json'
    path.write_text(json.dumps(RECORDS[:1]))
    assert saved(path) == {'elated-tan-skat': {'shortAlias': 'europa'}}


def test_apply_skips_unchanged(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path = tmp_path / 'upstreams.conf'
    path.write_text('same')
    monkeypatch.setattr(nginx, 'reload', lambda: pytest.fail('reloaded'))
    assert nginx.apply({path: 'same'})


def test_apply_restores_on_reject(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    kept, fresh = tmp_path / 'upstreams.conf', tmp_path / 'locations.conf'
    kept.write_text('old')
    monkeypatch.setattr(nginx, 'reload', lambda: False)
    assert not nginx.apply({kept: 'new', fresh: 'new'})
    assert (kept.read_text(), fresh.read_text()) == ('old', '')


def test_lag_boundary() -> None:
    chain = Chain('c', {}, tuple(Node(NodeId(i), 'n', 'ip', 'd', Port(10000)) for i in range(4)))
    stamps = dict(zip(chain.nodes, [1000, 1000 - MAX_LAG, 999 - MAX_LAG, -1], strict=True))
    assert healthy(chain, stamps) == {0, 1}
