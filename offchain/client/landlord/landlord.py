import asyncio
import sys
from pathlib import Path
import contextlib
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from common.client import Client
from common.constants import SIGN, LANDLORDSIG, PAYLOAD, ACTION, STARTRENTAL, STOPRENTAL, CONNECT

class LandlordClient(Client):
    def __init__(self):
        super().__init__("landlord")
        self.active = asyncio.Event()
        self.nonce = 0
        self.invoice_task = None
        self.INVOICE_INTERVAL = 5

    async def start_container(self):
        self.logger.info("starting container")
    
    async def stop_container(self):
        self.logger.info("stopping container")

    async def invoice_loop(self):
        try:
            while self.active.is_set():
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
                self.logger.info("sent invoice to renter...")

                self.nonce += 1
                await asyncio.sleep(5)
        except asyncio.CancelledError:
            self.logger.info("send invoices cancelled...")
            raise

    async def run(self):
        self.logger.info(f"active is set: {self.active.is_set()}")
        async for raw in self.websocket:
            message = self.deserialize(raw)
            action = message[ACTION]

            if action == STARTRENTAL and not self.active.is_set():
                self.logger.info("starting rental...")
                await self.start_container()
                self.active.set()
                self.invoice_task = asyncio.create_task(self.invoice_loop())
            elif action == STOPRENTAL and self.active.is_set():
                self.logger.info("stopping rental...")
                self.active.clear()
                if self.invoice_task:
                    self.invoice_task.cancel()
                    with contextlib.suppress(asyncio.CancelledError):
                        await self.invoice_task
                await self.stop_container()
                self.nonce = 0
            elif action == SIGN:
                self.logger.info(f"got signed invoice: {message[PAYLOAD]}")
                self.invoices.append(message[PAYLOAD])
            else:
                self.logger.warning("got an unknown action!")


