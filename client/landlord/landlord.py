from dotenv import load_dotenv
import os
import sys
from pathlib import Path
import json
from pathlib import Path
import websockets
import asyncio
from datetime import datetime

sys.path.append(str(Path(__file__).resolve().parent.parent))
from common.logger import get_logger

logger = get_logger("landlord")

global_env = Path('..') / '.env'
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=global_env)
load_dotenv(dotenv_path=env_path)

server = os.getenv("SERVER_URI")
public_key = os.getenv("PUBLIC_KEY")
private_key = os.getenv("PRIVATE_KEY")

from dotenv import load_dotenv
import os
import json
from pathlib import Path
import websockets
import asyncio

global_env = Path('..') / '.env'
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=global_env)
load_dotenv(dotenv_path=env_path)

server = os.getenv("SERVER_URI")
public_key = os.getenv("PUBLIC_KEY")
private_key = os.getenv("PRIVATE_KEY")

IDENTIFY = 'identify'
OPEN = 'open'
SIGN = 'sign'

vouchers = []

async def open_connection(uri: str) -> websockets.WebSocketClientProtocol:
    websocket = await websockets.connect(uri)
    msg = {
        "action": "identify",
        "pk": public_key
    }
    await websocket.send(json.dumps(msg))
    return websocket

async def send_message(ws, message: dict):
    await ws.send(json.dumps(message))

async def landlord_main():
    ws = await open_connection(server)

    await asyncio.sleep(2)

    while True:
        payload = { 
            "action": SIGN,
            "payload": {
                "type": "voucher",
                "amount": 3000,
                "nonce": str(datetime.now())
            },
            "signed": False
        }

        await send_message(ws, payload)

        response = await ws.recv()
        response_data = json.loads(response)

        logger.info(f"received response: {response_data}")

        vouchers.append(response_data)

        await asyncio.sleep(10)

asyncio.run(landlord_main())