import asyncio
import websockets
import json
import sys
from pathlib import Path
from web3 import Web3

sys.path.append(str(Path(__file__).resolve().parent.parent))

from common.logger import get_logger
from common.constants import *
from block_listener import watch_blocks

abi_path = Path(__file__).resolve().parent / "../Moderator.json"
with open(abi_path) as f:
    abi = json.load(f)["abi"]

provider = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))
if not provider.is_connected():
    raise Exception("web3 connection failed")

contract_address = "0x5FbDB2315678afecb367f032d93F642f64180aa3"
moderator = provider.eth.contract(address=contract_address, abi=abi)

admin_account = provider.eth.accounts[2]

channels = {}

pairing = {} # pk -> pk
pk_resolve = {} # pk -> ws
ws_resolve = {} # ws -> pk

logger = get_logger("server")

async def echo(websocket):
    async for message in websocket:
        await websocket.send(message)

async def handle(websocket):
    async for message in websocket:
        msg = json.loads(message)

        if msg[ACTION] == IDENTIFY:
            pk = msg[KEY]
            pk_resolve[pk] = websocket
            ws_resolve[websocket] = pk
            logger.info(f"identified {pk} with {websocket}")
        elif msg[ACTION] == OPEN:
            renter = msg[RENTER]
            landlord = msg[LANDLORD]
            pairing[renter] = landlord
            pairing[landlord] = renter
            try:
                tx_hash = moderator.functions.openChannel(renter, landlord).transact({
                    "from": admin_account,
                    "gas": 1_000_000
                })
                receipt = provider.eth.wait_for_transaction_receipt(tx_hash)
                event = moderator.events.ChannelOpened().process_receipt(receipt)[0]
                channel_id = event["args"]["channelId"]

                channels[(renter, landlord)] = channel_id
                logger.info(f"channel created: {channel_id.hex()} between {renter} and {landlord}")

                landlord_ws = pk_resolve[landlord]
                renter_ws = pk_resolve[renter]
                openmsg = {"action": STARTRENTAL, CHANNELID: channel_id.hex()}
                await landlord_ws.send(json.dumps(openmsg))
                await renter_ws.send(json.dumps(openmsg))
            except Exception as e:
                logger.error(f"failed to open channel: {e}")
        elif msg[ACTION] == STOPRENTAL:
            sender_pk = ws_resolve[websocket]
            recipient_pk = pairing[sender_pk]
            recipient_ws = pk_resolve[recipient_pk]
            closemsg = {"action": STOPRENTAL}
            await recipient_ws.send(json.dumps(closemsg))
            logger.info(f"closing channel {sender_pk} to {recipient_pk}")
        elif msg[ACTION] == SIGN:
            sender_pk = ws_resolve[websocket]
            recipient_pk = pairing[sender_pk]
            recipient_ws = pk_resolve[recipient_pk]
            await recipient_ws.send(message)
            logger.info(f"forwarded from {sender_pk} to {recipient_pk}")

async def main():
    asyncio.create_task(watch_blocks())
    async with websockets.serve(handle, "0.0.0.0", 8765):
        await asyncio.Future()  

asyncio.run(main())