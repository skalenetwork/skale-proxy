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
3. Export all required environement variables (see below)
4. Run `scripts/run_proxy.sh`

#### Required environement variables

- `NETWORKS`
- `DOCS_WEBSITE_URL`
- `MAIN_WEBSITE_URL`
- `NETWORK_NAME`
- `CHAIN_ID`
- `EXPLORER_URL`
- `BASE_PROXY_URL`
- `ETH_ENDPOINT`

## License

[![License](https://img.shields.io/github/license/skalenetwork/skale-proxy.svg)](LICENSE)

All contributions to SKALE Proxy are made under the [GNU Affero General Public License v3](https://www.gnu.org/licenses/agpl-3.0.en.html). See [LICENSE](LICENSE).

Copyright (C) 2022-Present SKALE Labs.
