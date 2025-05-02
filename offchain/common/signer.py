from web3 import Web3
from eth_account import Account
from eth_account.messages import encode_defunct

class ChannelSigner:
    def __init__(self, private_key: str):
        self.account = Account.from_key(private_key)

    def hash(self, channel_id: int, nonce: int) -> bytes:
        chan_b32 = channel_id.to_bytes(32, "big")   # 32‑byte big‑endian
        return Web3.solidity_keccak(
            ["bytes32", "uint32"],
            [chan_b32, nonce]
        )

    def sign(self, channel_id: int, nonce: int) -> str:
        voucher_hash = self.hash(channel_id, nonce)
        eth_message = encode_defunct(hexstr=voucher_hash.hex())
        signed_message = self.account.sign_message(eth_message)
        return signed_message.signature.hex()

    def verify(self, channel_id: int, nonce: int, signature: str) -> str:
        voucher_hash = self.hash(channel_id, nonce)
        eth_message = encode_defunct(hexstr=voucher_hash.hex())
        recovered = Account.recover_message(eth_message, signature=signature)
        return recovered
