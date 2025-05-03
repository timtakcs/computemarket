import argparse
import asyncio
import signal
import sys
import os
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent))

from landlord.landlord import LandlordClient
from renter.renter import RenterClient

def main():
    parser = argparse.ArgumentParser(description="Exchange CLI - Renter or Landlord")
    parser.add_argument('-l', '--landlord', action='store_true', help='Run as landlord')
    parser.add_argument('-r', '--renter', action='store_true', help='Run as renter')
    parser.add_argument("-id", "--landlord-id", type=str, help="Landlord public key")

    args = parser.parse_args()

    print("what the fuck please")

    if args.landlord: 
        landlord_pk = "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266"
        landlord_sk = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"
        os.environ["PUBLIC_KEY"]  = landlord_pk
        os.environ["PRIVATE_KEY"] = landlord_sk
        client = LandlordClient()
    elif args.renter:
        if not args.landlord_id:
            raise ValueError("You must specify --landlord-id when using -r")
        client = RenterClient(args={"landlordpk": args.landlord_id})
    else:
        print("Error: You must specify --landlord or --renter.")
        return

    async def runner():
        stop_called = asyncio.Event()

        async def shutdown():
            if not stop_called.is_set():
                stop_called.set()
                await client.stop()
                await asyncio.sleep(0.1)  
                loop.stop()

        loop = asyncio.get_running_loop()
        loop.add_signal_handler(signal.SIGINT, lambda: asyncio.create_task(shutdown()))

        await client.start()
        await stop_called.wait()

    asyncio.run(runner())

if __name__ == "__main__":
    main()
