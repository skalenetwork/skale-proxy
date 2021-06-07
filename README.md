# skale-proxy

skale-proxy is a public service that provides proxied and load-balanced JSON-RPC endpoints for SKALE chains 


# running

1. Set `FULL_PROXY_DOMAIN_NAME` and `ETH_ENDPOINT` in .env to the domain name of your proxy, and run `source .env`.

2. Copy server.crt and server.key to the `data/` directory. The certificate needs to be issued to `FULL_PROXY_DOMAIN_NAME`.

3. Ensure the correct ABI of SKALE Manager is placed in the `abi/` folder.

3. Simply run

`docker-compose pull && docker-compose up`

And then wait until skale-proxy reads schain info from blockchain and starts.

# local development

Set `FULL_PROXY_DOMAIN_NAME` to localhost and run `cert_gen.sh`. This will generate a self-signed cert in the `data/` directory.

