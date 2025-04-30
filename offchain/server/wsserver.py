import asyncio
import websockets
import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
from common.logger import get_logger
from common.constants import *

pairing = {} # pk -> pk
pk_resolve = {} # pk -> ws
ws_resolve = {} # ws -> pk

logger = get_logger("server")

# pairing['0xada6710E3951ee357825baBB84cE06300B13c073'] = '0x939d31bD382a5B0D536ff45E7d086321738867a2'
# pairing['0x939d31bD382a5B0D536ff45E7d086321738867a2'] = '0xada6710E3951ee357825baBB84cE06300B13c073'

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
            landlord_ws = pk_resolve[landlord]
            openmsg = {"action": STARTRENTAL}
            await landlord_ws.send(json.dumps(openmsg))
            logger.info(f"create channel between {renter} and {landlord}")
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
    async with websockets.serve(handle, "0.0.0.0", 8765):
        await asyncio.Future()  

asyncio.run(main())