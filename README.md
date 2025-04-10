# SKALE Proxy

[![Discord](https://img.shields.io/discord/534485763354787851.svg)](https://discord.gg/vvUtWJB)

SKALE Proxy is high performance, easy-to-run public service that provides proxied and load-balanced
JSON-RPC endpoints for SKALE chains. It is based on NGINX.

## Usage guide

### Prerequisites

- Docker
- docker-compose

### Repo setup

1. Clone repo & all submodules
2. Put `abi.json`, `server.crt` and `server.key`files in `data` folder
3. Export all required environment variables (see below)
4. Run `scripts/run_proxy.sh`

#### Pre-commit hook

```bash
ruff check --config metrics/pyproject.toml metrics/src/
```

#### Format code

```bash
ruff format src/
```

#### Required environment variables

- `ETH_ENDPOINT` - endpoint of the Ethereum network where `skale-manager` contracts are deployed

#### Optional environment variables

- `HEARTBEAT_URL` - URL for healthcheck endpoint (optional)
- `USE_ALB` - Set to `True` if the proxy is deployed behind a load balancer (like AWS ALB) that sets the `X-Forwarded-For` header. This configures Nginx to correctly identify the client's real IP address for rate limiting. Defaults to `False` if not set.

## License

[![License](https://img.shields.io/github/license/skalenetwork/skale-proxy.svg)](LICENSE)

All contributions to SKALE Proxy are made under the [GNU Affero General Public License v3](https://www.gnu.org/licenses/agpl-3.0.en.html). See [LICENSE](LICENSE).

Copyright (C) 2022-Present SKALE Labs.
