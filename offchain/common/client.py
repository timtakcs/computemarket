import os
import json
import asyncio
from pathlib import Path
import websockets.client
from dotenv import load_dotenv
from web3 import Web3
from eth_account import Account
from eth_account.messages import encode_defunct
from eth_utils import to_bytes

from common.logger import get_logger
from common.constants import IDENTIFY, CHANNELID, NONCE
from common.signer import ChannelSigner

abi_path = Path(__file__).resolve().parent / "../Moderator.json"
with open(abi_path) as f:
    abi = json.load(f)["abi"]

provider = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))
if not provider.is_connected():
    raise Exception("Web3 connection failed")

env_path = Path('..') / '.env'
load_dotenv(dotenv_path=env_path)
contract_address = os.getenv("CONTRACT_ADDRESS")
moderator = provider.eth.contract(address=contract_address, abi=abi)

class Client:
    def __init__(self, role: str):
        self.logger = get_logger(role)
        self.role = role
        self.websocket = None

        self.channel = None
        self.invoices = []

        env_path = Path('..') / '.env'
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
    
    async def submit_invoice_to_contract(self):
        if not self.channel:
            self.logger.error("cannot submit: channel ID not set")
            return
        if not self.invoices:
            self.logger.error("cannot submit: no invoices to submit")
            return

        last_invoice = self.invoices[-1]
        nonce = int(last_invoice[NONCE])
        sigR_raw = last_invoice.get("sigR", "")
        sigL_raw = last_invoice.get("sigL", "")

        if not isinstance(sigR_raw, str) or not isinstance(sigL_raw, str):
            self.logger.error("invalid signature format in invoice")
            return

        sigR = bytes.fromhex(sigR_raw)
        sigL = bytes.fromhex(sigL_raw)

        self.logger.info(f"contract at {contract_address}")

        try:
            channel_id_bytes = self.channel.to_bytes(32, "big")

            tx_hash = moderator.functions.submitInvoice(
                channel_id_bytes,
                nonce,
                sigL,
                sigR
            ).transact({
                "from": self.public_key,
                "gas": 1_000_000
            })

            receipt = provider.eth.wait_for_transaction_receipt(tx_hash)
            self.logger.info(f"submitted invoice to contract (nonce {nonce})")
        except Exception as e:
            self.logger.error(f"failed to submit invoice: {e}")

    async def run(self):
        """Override this in subclass"""
        raise NotImplementedError("Subclasses must implement run() method.")

    async def start(self):
        await self.connect()
        await self.run()
