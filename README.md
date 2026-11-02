# SKALE Proxy

Public JSON-RPC, WebSocket and filestorage endpoints for SKALE chains, load-balanced by nginx.

- `nginx`: the official image with a static config. Serves `/v1/<chain>`, `/v1/ws/<chain>`, `/fs/<chain>` and `/files/`.
- `proxy`: every 10 minutes discovers chains from `skale-manager`, probes nodes, writes `conf/*.conf` and `www/chains.json`, and reloads nginx when the config changes.
- `metrics` (`COMPOSE_PROFILES=metrics`): explorer counters and stats into SQLite, published as `/files/metrics.json`.

## Environment

| Variable | Service | Required | Description |
|---|---|---|---|
| `ENDPOINT` | proxy | yes | Ethereum RPC where `skale-manager` is deployed |
| `MANAGER_CONTRACTS` | proxy | yes | `skale-manager` address or alias |
| `NETWORK_NAME` | proxy, metrics | yes | SKALE network name; metrics supports `mainnet`, `testnet`, `legacy` and `regression` |
| `USE_ALB` | nginx | yes | `True` behind an AWS ALB (trusts `X-Forwarded-For` from RFC 1918 ranges), `False` otherwise |
| `HEARTBEAT_URL` | proxy | no | URL requested after each complete discovery |
| `ETH_ENDPOINT` | metrics | with `metrics` | Ethereum RPC for the gas price |

## Run

Put `server.crt` and `server.key` in `data/`, export the environment, then:

```bash
docker compose up -d --build --remove-orphans
```

## Develop

`uv sync --locked`, then the checks in `.github/workflows/ci.yml`: ruff, mypy, pytest and `nginx -t` against `tests/golden`.

## License

[GNU Affero General Public License v3](LICENSE). Copyright (C) 2022-Present SKALE Labs.
