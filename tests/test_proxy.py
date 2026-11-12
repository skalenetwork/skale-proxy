import io
import json
import re
from pathlib import Path
from time import sleep
from types import SimpleNamespace
from typing import NoReturn, cast

import pytest
import requests
from skale import SkaleManager
from skale.types.node import NodeId, Port

from proxy import nginx
from proxy.__main__ import saved
from proxy.chains import (
    MAX_BODY,
    MAX_LAG,
    Chain,
    Node,
    block_field,
    chain_record,
    discover,
    healthy,
    node_data,
    probe,
)

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


@pytest.mark.parametrize(
    'alias', ['', 'e;}', 'europa\n', 'europa/x', 'Europa', 'e' * 254, ['europa']]
)
def test_render_skips_unsafe_names(alias: object) -> None:
    hostile = Chain('x;}', {'name': 'x;}', 'schain_hash': 'ab'}, NODES)
    aliased = chain_record(CHAIN, STAMPS, {'elated-tan-skat': {'shortAlias': alias}})
    assert nginx.render([chain_record(hostile, STAMPS, {}), aliased]) == nginx.render(
        [chain_record(CHAIN, STAMPS, {})]
    )


def test_render_keeps_names_unique() -> None:
    names = ('foo', 'ws-foo', 'bar', 'baz')
    chains = [Chain(n, {'name': n, 'schain_hash': 'ab'}, NODES) for n in names]
    metadata = {
        'foo': {'shortAlias': 'bar'},
        'ws-foo': {'shortAlias': 'ws-foo'},
        'bar': {'shortAlias': 'eu'},
        'baz': {'shortAlias': 'eu'},
    }
    files = nginx.render([chain_record(c, STAMPS, metadata) for c in chains])
    ups = re.findall(r'^upstream (\S+)', files[nginx.CONF / 'upstreams.conf'], re.M)
    assert len(ups) == len(set(ups)) == 12
    routes = [('foo', 'foo'), ('bar', 'foo'), ('ws-foo', 'ws-foo'), ('eu', 'baz'), ('baz', 'baz')]
    assert files[nginx.CONF / 'locations.conf'] == ''.join(nginx.locations(*r) for r in routes)


@pytest.mark.parametrize(
    ('domain', 'valid'),
    [
        ('node-1.skale.example.com', True),
        ('10.0.0.1', True),
        ('node_2.example.com.', True),
        ('a' * 254, False),
        ('a.example;\n}', False),
        ('a.example\n', False),
        ('a.example:80', False),
        ('a example', False),
    ],
)
def test_node_data_checks_domain(domain: str, valid: bool) -> None:
    node = {'name': 'a', 'ip': bytes(4), 'domain_name': domain, 'port': 10000}
    skale = SimpleNamespace(
        nodes=SimpleNamespace(get=lambda _: node),
        schains_internal=SimpleNamespace(schain_hashes_for_node=lambda _: []),
    )
    assert (node_data(cast(SkaleManager, skale), NodeId(1)) is not None) is valid


def test_discover_skips_non_utf8_strings() -> None:
    def fail(_: object) -> NoReturn:
        raise UnicodeDecodeError('utf-8', b'\xff', 0, 1, 'invalid start byte')

    schain = SimpleNamespace(name='good', to_dict=lambda: {'name': 'good'})
    node = {'name': 'a', 'ip': bytes(4), 'domain_name': 'a.example', 'port': 10000}
    skale = SimpleNamespace(
        schains_internal=SimpleNamespace(
            all_schain_hashes=lambda: [b'good', b'bad'],
            node_ids_for_schain_hash=lambda _: [1, 2],
            schain_hashes_for_node=lambda _: [b'good', b'bad'],
        ),
        schains=SimpleNamespace(get=lambda h: schain if h == b'good' else fail(h)),
        nodes=SimpleNamespace(get=lambda i: node if i == 1 else fail(i)),
    )
    chains = discover(cast(SkaleManager, skale))
    assert [(c.name, [n.id for n in c.nodes]) for c in chains] == [('good', [1])]


def test_chains_json_matches_golden() -> None:
    assert json.loads((GOLDEN / 'chains.json').read_text()) == RECORDS


def test_saved_roundtrip(tmp_path: Path) -> None:
    path = tmp_path / 'chains.json'
    assert saved(path) == {}
    path.write_text(json.dumps(RECORDS))
    assert saved(path) == {'elated-tan-skat': {'shortAlias': 'europa'}}


def test_apply_skips_unchanged(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path = tmp_path / 'upstreams.conf'
    path.write_text('same')
    monkeypatch.setattr(nginx, 'reload', lambda: pytest.fail('reloaded'))
    assert nginx.apply({path: 'same'})


@pytest.mark.parametrize(('reloaded', 'expected'), [(True, ('new', 'new')), (False, ('old', ''))])
def test_apply_keeps_accepted_config(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, reloaded: bool, expected: tuple[str, str]
) -> None:
    kept, fresh = tmp_path / 'upstreams.conf', tmp_path / 'locations.conf'
    kept.write_text('old')
    monkeypatch.setattr(nginx, 'reload', lambda: reloaded)
    assert nginx.apply({kept: 'new', fresh: 'new'}) is reloaded
    assert (kept.read_text(), fresh.read_text()) == expected


@pytest.mark.parametrize(('answer', 'left'), [('ok', 'ok'), ('failed', 'failed'), ('reload', '')])
def test_reload_waits_for_nginx_answer(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, answer: str, left: str
) -> None:
    monkeypatch.setattr(nginx, 'STATUS', tmp_path / 'status')
    nginx.STATUS.write_text('ok')
    monkeypatch.setattr(
        'proxy.nginx.time.sleep',
        lambda _: nginx.STATUS.read_text() == 'reload' and nginx.STATUS.write_text(answer),
    )
    assert nginx.reload() is (answer == 'ok')
    assert nginx.STATUS.read_text() == left


def test_unhealthy_chain_routes_all_nodes(caplog: pytest.LogCaptureFixture) -> None:
    info = chain_record(CHAIN, dict.fromkeys(NODES, -1), {})['chain_info']
    assert info['fs_endpoints'] == ['127.0.0.1', '127.0.0.2']
    assert caplog.messages == [
        'Leaving out node a (127.0.0.1) of elated-tan-skat: block ts -1, chain head 0',
        'Leaving out node b (127.0.0.2) of elated-tan-skat: block ts -1, chain head 0',
        'No healthy node in elated-tan-skat, routing to all of its nodes',
    ]


@pytest.mark.parametrize(
    ('stamps', 'expected'),
    [
        ([1000, 1000, 1000, 1000 - MAX_LAG, 999 - MAX_LAG, -1], [0, 1, 2, 3]),
        ([1000, 10**12], [0, 1]),
    ],
)
def test_healthy(stamps: list[int], expected: list[int]) -> None:
    nodes = tuple(Node(NodeId(i), 'n', 'ip', 'd', Port(10000)) for i in range(len(stamps)))
    chain = Chain('c', {}, nodes)
    assert [n.id for n in healthy(chain, dict(zip(nodes, stamps, strict=True)))] == expected


def test_probe_gives_up_on_slow_nodes(monkeypatch: pytest.MonkeyPatch) -> None:
    def block_field(_: object, url: str, __: str) -> int:
        if url.endswith(':10131'):
            sleep(1)
        return 1

    monkeypatch.setattr('proxy.chains.PROBE_TIMEOUT', 0.1)
    monkeypatch.setattr('proxy.chains.block_field', block_field)
    assert probe(requests.Session(), [CHAIN]) == {NODES[0]: 1, NODES[1]: -1}


@pytest.mark.parametrize(
    ('body', 'expected'),
    [
        (b'{"result": {"timestamp": "0x10"}}', 16),
        (b'[' * 100_000, None),
        (b'{"result": {"timestamp": "0x%s"}}' % (b'7' * 3600), None),
        (b' ' * (MAX_BODY + 1), None),
    ],
)
def test_block_field_rejects_hostile_bodies(body: bytes, expected: int | None) -> None:
    response = requests.Response()
    response.status_code, response.raw = 200, io.BytesIO(body)
    session = SimpleNamespace(post=lambda *_, **__: response)
    assert block_field(cast(requests.Session, session), 'http://n', 'timestamp') == expected
