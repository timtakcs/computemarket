import argparse
import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent))

from landlord.landlord import LandlordClient
from renter.renter import RenterClient

def main():
    parser = argparse.ArgumentParser(description="Exchange CLI - Renter or Landlord")
    parser.add_argument('-l', '--landlord', action='store_true', help='Run as landlord')
    parser.add_argument('-r', '--renter', action='store_true', help='Run as renter')

    args = parser.parse_args()

    if args.landlord:
        client = LandlordClient()
        client.public_key = "0x939d31bD382a5B0D536ff45E7d086321738867a2"
        client.private_key = "5af990b93cd5a5985cef57dc599eff96257b16751f0256a1ce8669d1277fa30e"
    elif args.renter:
        client = RenterClient()
    else:
        print("Error: You must specify --landlord or --renter.")
        return

    asyncio.run(client.start())

if __name__ == "__main__":
    main()
