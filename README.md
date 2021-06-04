# Skale-proxy

skale-proxy is a public service that provides proxied and load-balanced JSON-RPC endpoints for SKALE chains.

It is based on Nginx reverse proxy that receives SKALE chain names and IP addresses of SKALE nodes from SKALE manager. 

# Endpoints

For SKALE mainnet the endpoints that proxy provides are in the form of 

http://proxy.skale.network/mainnet/CHAIN_NAME

or

https://proxy.skale.network/mainnet/CHAIN_NAME

For SKALE testnet the endpoints that proxy provides are in the form of 

http://proxy.skale.network/testnet/CHAIN_NAME

or

https://proxy.skale.network/testnet/CHAIN_NAME


