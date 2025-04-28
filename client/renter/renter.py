from dotenv import load_dotenv
import os
import sys
from pathlib import Path
import json
from pathlib import Path
import websockets
import asyncio

sys.path.append(str(Path(__file__).resolve().parent.parent))
from common.logger import get_logger

logger = get_logger("renter")

global_env = Path('..') / '.env'
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=global_env)
load_dotenv(dotenv_path=env_path)

server = os.getenv("SERVER_URI")
public_key = os.getenv("PUBLIC_KEY")
private_key = os.getenv("PRIVATE_KEY")

IDENTIFY = 'identify'
SIGN = 'sign'

vouchers = []

async def open_connection(uri: str) -> websockets.WebSocketClientProtocol:
    websocket = await websockets.connect(uri)
    msg = {
        "action": IDENTIFY,
        "pk": public_key
    }
    await websocket.send(json.dumps(msg))
    return websocket

async def send_message(ws, message: dict):
    await ws.send(json.dumps(message))

async def renter_main():
    ws = await open_connection(server)

    await asyncio.sleep(5)

    async for message in ws:
        new_voucher = json.loads(message)
        new_voucher['signed'] = True
        vouchers.append(new_voucher)

        logger.info(f"received invoice: {new_voucher}")
        
        response = json.dumps(new_voucher)
        await ws.send(response)

asyncio.run(renter_main())
