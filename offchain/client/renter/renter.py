import asyncio
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from common.client import Client
from common.constants import *

LANDLORDPK = 'landlordpk'

class RenterClient(Client):
    def __init__(self, args = {}):
        super().__init__("renter")
        self.invoices = [] 
        self.args = args
        self._stop_event = asyncio.Event()

    async def request_connection(self, landlord_pk: str):
        msg = {
            "action": OPEN,
            RENTER: self.public_key,
            LANDLORD: landlord_pk
        }
        await self.send_message(msg)
        self.logger.info(f"sent open request to {landlord_pk}")
    
    async def send_stop_rental(self):
        msg = {
            "action": STOPRENTAL
        }
        await self.send_message(msg)
        self.logger.info(f"received kill signal, stopping rental...")

    async def run(self):
        await self.request_connection(self.args[LANDLORDPK])

        async for message in self.websocket:
            if self._stop_event.is_set():
                break

            json_message = self.deserialize(message)
            new_invoice = json_message[PAYLOAD]
            sigR = self.sign(new_invoice)

            new_invoice[RENTERSIG] = sigR
            self.invoices.append(new_invoice)
            
            self.logger.info(f"received invoice: {new_invoice}")
            json_message[PAYLOAD] = new_invoice

            await self.send_message(json_message)
    
    async def stop(self):
        if self.websocket:
            await self.send_stop_rental()
            await self.websocket.close()
            self.logger.info("renter client shutdown complete!")
        self._stop_event.set()

