import json

import requests
from tqdm import tqdm


rpc_endpoint = ''


def fetch_gas_used(block_number):
    request = {
        "jsonrpc": "2.0",
        "method": "eth_getBlockByNumber",
        "params": [block_number, False],
        "id": 1
    }
    res = requests.post(rpc_endpoint, json=request).json()
    return res['result']['hash'], int(res['result']['gasUsed'], 16)

gas_used_dict = dict()

for i in tqdm(range(10)):
    hash, gas_used = fetch_gas_used(i)
    gas_used_dict[hash.lower()] = gas_used

with open('base_gas_used.json', 'w') as f:
    json.dump(gas_used_dict, f)

