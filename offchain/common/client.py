import os
import json
import asyncio
from pathlib import Path
import websockets.client
from dotenv import load_dotenv

from common.logger import get_logger
from common.constants import IDENTIFY, CHANNELID, NONCE
from common.signer import ChannelSigner

class Client:
    def __init__(self, role: str):
        self.logger = get_logger(role)
        self.role = role
        self.websocket = None

        self.invoices = []

        env_path = Path('.') / '.env'
        load_dotenv(dotenv_path=env_path)

        self.server_uri = os.getenv("SERVER_URI")
        self.public_key = os.getenv("PUBLIC_KEY")
        self.private_key = os.getenv("PRIVATE_KEY")

        self.signer = ChannelSigner(self.private_key)
    
    def deserialize(self, message: str) -> dict:
        return json.loads(message)
    
    def sign(self, invoice: dict):
        channel_id = int(invoice[CHANNELID])
        nonce = int(invoice[NONCE])
        
        if len(self.invoices) and nonce <= self.invoices[-1][NONCE]:
            self.logger.error("invalid nonce")
            return '0' # not a good solution, but for now just return invalid signature
    
        signature = self.signer.sign(channel_id, nonce)
        return signature

    async def connect(self):
        self.websocket = await websockets.client.connect(self.server_uri)
        await self.identify()

    async def identify(self):
        msg = {
            "action": IDENTIFY,
            "pk": self.public_key
        }
        await self.send_message(msg)

    async def send_message(self, message: dict):
        await self.websocket.send(json.dumps(message))

    async def receive_message(self) -> dict:
        response = await self.websocket.recv()
        return json.loads(response)

    async def run(self):
        """Override this in subclass"""
        raise NotImplementedError("Subclasses must implement run() method.")

    async def start(self):
        await self.connect()
        await self.run()
