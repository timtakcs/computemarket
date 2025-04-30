import argparse
import asyncio
import signal
import sys
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

    if args.landlord:
        client = LandlordClient()
        client.public_key = "0x939d31bD382a5B0D536ff45E7d086321738867a2"
        client.private_key = "5af990b93cd5a5985cef57dc599eff96257b16751f0256a1ce8669d1277fa30e"
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
                await asyncio.sleep(0.1)  # allow logs to flush
                loop.stop()

        loop = asyncio.get_running_loop()
        loop.add_signal_handler(signal.SIGINT, lambda: asyncio.create_task(shutdown()))

        await client.start()
        await stop_called.wait()

    asyncio.run(runner())

if __name__ == "__main__":
    main()
