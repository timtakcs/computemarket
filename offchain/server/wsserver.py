import asyncio
import websockets
import json
import sys
from pathlib import Path
from web3 import Web3

sys.path.append(str(Path(__file__).resolve().parent.parent))

from common.logger import get_logger
from common.constants import *

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
submitted_channels = {}

pairing = {} # pk -> pk
pk_resolve = {} # pk -> ws
ws_resolve = {} # ws -> pk

logger = get_logger("server")

async def watch_blocks():
    last_block = provider.eth.block_number
    while True:
        current_block = provider.eth.block_number
        if current_block > last_block:
            logger.info(f"block {current_block} mined")
            to_remove = []
            for channel_id, expiration in submitted_channels.items():
                if current_block >= expiration:
                    try:
                        tx = moderator.functions.closeChannel(channel_id).transact({
                            "from": admin_account,
                            "gas": 500_000
                        })
                        provider.eth.wait_for_transaction_receipt(tx)
                        logger.info(f"channel {channel_id.hex()} closed successfully")
                        to_remove.append(channel_id)
                    except Exception as e:
                        logger.error(f"failed to close channel {channel_id.hex()}: {e}")
            for cid in to_remove:
                del submitted_channels[cid]

            last_block = current_block

        await asyncio.sleep(1.5)

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
            sender_pk    = ws_resolve[websocket]
            recipient_pk = pairing[sender_pk]
            recipient_ws = pk_resolve[recipient_pk]

            await recipient_ws.send(json.dumps({"action": STOPRENTAL}))
            logger.info(f"closing channel {sender_pk} to {recipient_pk}")

            chan_id = channels.get((sender_pk, recipient_pk)) or channels.get((recipient_pk, sender_pk))
            if chan_id:
                try:
                    chan_id_bytes = Web3.to_bytes(hexstr=chan_id.hex() if isinstance(chan_id, bytes) else chan_id)
                    data = moderator.functions.channels(chan_id_bytes).call()
                    expiration = data[4]                  
                    if expiration != 0:
                        submitted_channels[chan_id_bytes] = expiration
                        logger.info(f"registered {chan_id.hex()} expiring at block {expiration}")
                except Exception as e:
                    logger.error(f"failed to fetch expiration block: {e}")
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