# skale-proxy

skale-proxy is a public service that provides proxied and load-balanced JSON-RPC endpoints for SKALE chains 


# running

1. Set FULL_PROXY_DOMAIN_NAME in docker-compose to the domain name of your proxy.

2. create datadir and copy server.crt and server.key to it. The certificate need to be issued to FULL_PROXY_DOMAIN_NAME.

3. Simply run

docker-compose pull && docker-compose up

And then wait until skale-proxy reads schain info from blockchain and starts.

# local development

Set FULL_PROXY_DOMAIN_NAME to localhost and run cert_gen.sh. This will generate a self-signed cert. 

