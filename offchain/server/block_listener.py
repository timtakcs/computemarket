import asyncio
import json
from web3 import Web3

from pathlib import Path

abi_path = Path(__file__).resolve().parent / "../Moderator.json"
with open(abi_path) as f:
    abi = json.load(f)["abi"]

provider = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))
if not provider.is_connected():
    raise Exception("web3 connection failed")

address = "0x9fE46736679d2D9a65F0992F2272dE9f3c7fa6e0"
moderator = provider.eth.contract(address=address, abi=abi)

async def watch_blocks():
    block_filter = provider.eth.filter("latest")

    while True:
        for block_hash in block_filter.get_new_entries():
            block = provider.eth.get_block(block_hash)
            print(f"block {block.number} mined")
        await asyncio.sleep(1)
