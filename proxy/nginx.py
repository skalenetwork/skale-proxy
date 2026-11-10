import logging
import os
import re
import signal
import time
from collections.abc import Iterable
from contextlib import suppress
from pathlib import Path

from proxy.chains import ChainRecord, atomic_write

logger = logging.getLogger(__name__)

CONF = Path('/app/conf')
NAME = re.compile(r'[a-z0-9_-]{1,253}')


def upstream(name: str, servers: Iterable[str]) -> str:
    servers_conf = ''.join(f'    server {s} max_conns=4000 resolve;\n' for s in servers)
    return f'upstream {name} {{\n    zone {name} 64k;\n    ip_hash;\n{servers_conf}}}\n'


def locations(alias: str, name: str) -> str:
    return f"""location /v1/{alias} {{
    proxy_next_upstream error timeout non_idempotent;
    proxy_next_upstream_tries 2;
    proxy_next_upstream_timeout 10s;
    proxy_pass http://http-{name}/;
}}
location /v1/ws/{alias} {{
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection upgrade;
    proxy_pass http://ws-{name}/;
}}
location /fs/{alias} {{
    rewrite /fs/{alias}/(.*) /{name}/$1 break;
    proxy_pass http://storage-{name}/;
}}
"""


def render(chains: Iterable[ChainRecord]) -> dict[Path, str]:
    ups: list[str] = []
    routes: dict[str, str] = {}
    for chain in chains:
        info = chain['chain_info']
        if not info['http_endpoints']:
            continue
        name = info['schain_name']
        if not NAME.fullmatch(name):
            logger.warning('Skipping chain %.100r with an invalid name', name)
            continue
        ups += [
            upstream(f'http-{name}', info['http_endpoints']),
            upstream(f'ws-{name}', info['ws_endpoints']),
            upstream(f'storage-{name}', info['fs_endpoints']),
        ]
        routes.setdefault(name, name)
        alias = (chain['chain_metadata'] or {}).get('shortAlias')
        if isinstance(alias, str) and NAME.fullmatch(alias):
            routes[alias] = name
        elif alias:
            logger.warning('Skipping alias %.100r of %s with an invalid name', alias, name)
    locs = [locations(a, name) for a, name in routes.items()]
    return {CONF / 'upstreams.conf': ''.join(ups), CONF / 'locations.conf': ''.join(locs)}


def master() -> int | None:
    for cmdline in Path('/proc').glob('[0-9]*/cmdline'):
        with suppress(FileNotFoundError, ProcessLookupError):
            if cmdline.read_bytes().startswith(b'nginx: master process'):
                return int(cmdline.parent.name)
    return None


def workers(pid: int) -> set[int]:
    return {int(p) for p in Path(f'/proc/{pid}/task/{pid}/children').read_text().split()}


def reload() -> bool:
    if (pid := master()) is None:
        return False
    before = workers(pid)
    os.kill(pid, signal.SIGHUP)
    for _ in range(50):
        with suppress(FileNotFoundError, ProcessLookupError):
            if all(
                b'shutting down' in Path(f'/proc/{p}/cmdline').read_bytes()
                for p in before & workers(pid)
            ):
                return True
        time.sleep(0.2)
    return False


def apply(files: dict[Path, str]) -> bool:
    old = {path: path.read_text() if path.exists() else '' for path in files}
    if old == files:
        return True
    for path, text in files.items():
        atomic_write(path, text)
    if reload():
        logger.info('nginx reloaded')
        return True
    for path, previous in old.items():
        atomic_write(path, previous)
    logger.error('nginx rejected the new config, previous config restored')
    return False
