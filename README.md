# Skale-proxy

skale-proxy is a public service that provides proxied and load-balanced JSON-RPC endpoints for SKL chains.

It is based on Nginx reverse proxy that receives SKALE chain names and IP addresses of SKL nodes from SKALE manager. 

# Endpoints

For SKALE mainnet the endpoints that proxy provides are in the form of 

http://proxy.skale.network/mainnet/CHAIN_NAME

or

https://proxy.skale.network/mainnet/CHAIN_NAME

For SKL testnet the endpoints that proxy provides are in the form of 

http://proxy.skale.network/testnet/CHAIN_NAME

or

https://proxy.skale.network/testnet/CHAIN_NAME



# running

Simply run

docker-compose pull
docker-compuse up


And then wait until skale-proxy reads schain info from blockchain and starts