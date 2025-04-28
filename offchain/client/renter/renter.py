import asyncio
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from common.client import Client
from common.constants import CHANNELID, NONCE, PAYLOAD, RENTERSIG

class RenterClient(Client):
    def __init__(self):
        super().__init__("renter")
        self.invoices = [] 

    async def run(self):
        async for message in self.websocket:
            json_message = self.deserialize(message)

            new_invoice = json_message[PAYLOAD]
            sigR = self.sign(new_invoice)
            new_invoice[RENTERSIG] = sigR
            self.invoices.append(new_invoice)
            
            self.logger.info(f"received invoice: {new_invoice}")
            json_message[PAYLOAD] = new_invoice

            await self.send_message(json_message)

# client = RenterClient()
# asyncio.run(client.start())
