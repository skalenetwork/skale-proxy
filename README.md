# SKALE Proxy

Public JSON-RPC, WebSocket and filestorage endpoints for SKALE chains, load-balanced by nginx.

- `nginx`: the official image with a static config. Serves `/v1/<chain>`, `/v1/ws/<chain>`, `/fs/<chain>` and `/files/`. `config/reload.sh` runs inside it: when `proxy` asks through the `reload` volume, it runs `nginx -t` and reloads nginx.
- `proxy`: every 10 minutes discovers chains from `skale-manager`, probes nodes, writes `conf/*.conf` and `www/chains.json`, and reloads nginx when the config changes. If no node of a chain passes the probe, it routes to all of the chain's nodes instead of dropping the chain.
- `metrics` (`COMPOSE_PROFILES=metrics`): explorer counters and stats into SQLite, published as `/files/metrics.json`. After a cut-over from v2 the 7- and 30-day windows fill up over 30 days, because v2's MySQL history is not migrated.

## Environment

| Variable | Service | Required | Description |
|---|---|---|---|
| `ENDPOINT` | proxy | yes | Ethereum RPC where `skale-manager` is deployed |
| `MANAGER_CONTRACTS` | proxy | yes | `skale-manager` address or alias |
| `NETWORK_NAME` | proxy, metrics | yes | SKALE network name; metrics supports `mainnet`, `testnet`, `legacy` and `regression` |
| `USE_ALB` | nginx | yes | `True` behind an AWS ALB (trusts `X-Forwarded-For` from RFC 1918 ranges), `False` otherwise |
| `HEARTBEAT_URL` | proxy | no | URL requested after each successful discovery that nginx is serving |
| `ETH_ENDPOINT` | metrics | with `metrics` | Ethereum RPC for the gas price |

## Run

Put `server.crt` and `server.key` in `data/` and the environment in `.env`, then:

```bash
docker compose up -d --build --remove-orphans
```

## Develop

`uv sync --locked`, then the checks in `.github/workflows/ci.yml`: ruff, mypy, pytest and `nginx -t` against `tests/golden`.

## License

[GNU Affero General Public License v3](LICENSE). Copyright (C) 2022-Present SKALE Labs.
