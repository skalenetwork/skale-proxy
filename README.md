# SKALE Proxy

[![Discord](https://img.shields.io/discord/534485763354787851.svg)](https://discord.gg/vvUtWJB)

SKALE Proxy is high performance, easy-to-run public service that provides proxied and load-balanced 
JSON-RPC endpoints for SKALE chains. It is based on NGINX.

## Usage guide

### Prerequisites

- Docker
- docker-compose


### Repo setup

1. Clone all submodules  
2. Put `abi.json` file in `data` folder  
3. Put `server.crt` and `server.key` files in `data` folder
4. Configure proxy-ui environement params
5. Export `ENDPOINT` environement param
5. Run ` docker-compose up --build`

1. Place you ABI json file into abi directory

2. Set 'ABI_FILENAME directory' in docker-compose.yml to the name of the ABI file.
      
3. Set 'PROXY_FULL_HOST_NAME' in docker-compose.yml to the domain name of your proxy.

4. Set 'ENDPOINT_PREFIX' in 'docker-compose.yml' to the endpoint prefix (must be non-empty!)

5. Set 'ETH_ENDPOINT' in docker-compose to your ETH main net endpoint.

6. Create 'data' directory and copy 'server.crt' and 'server.key' to it. 
   The certificate need to be issued to 'PROXY_FULL_HOST_NAME'.

  
7. Run 'docker-compose pull && docker-compose up'  andf wait around a minute until skale-proxy reads schain info from blockchain and starts.

8.  Try 'http://PROXY_FULL_HOST_NAME/api.json' . You should be able to see API descriptions. 

 Voila!

## License

[![License](https://img.shields.io/github/license/skalenetwork/skale-admin.svg)](LICENSE)

All contributions to SKALE Admin are made under the [GNU Affero General Public License v3](https://www.gnu.org/licenses/agpl-3.0.en.html). See [LICENSE](LICENSE).

Copyright (C) 2022-Present SKALE Labs.