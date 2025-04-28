import asyncio
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from common.client import Client
from common.constants import SIGN, LANDLORDSIG, PAYLOAD

class LandlordClient(Client):
    def __init__(self):
        super().__init__("landlord")
        self.idle = asyncio.Event()
        self.nonce = 0

    async def run(self):
        while True:
            invoice = {
                "action": SIGN,
                "payload": {
                    "nonce": self.nonce,
                    "channel_id": 1
                }
            }

            sigL = self.sign(invoice[PAYLOAD])
            invoice[LANDLORDSIG] = sigL

            await self.send_message(invoice)
            response = await self.receive_message()

            self.logger.info(f"received invoice: {response}")
            self.invoices.append(response[PAYLOAD])

            self.nonce += 1

            await asyncio.sleep(5)

# client = LandlordClient()
# asyncio.run(client.start())
