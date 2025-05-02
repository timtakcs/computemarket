// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.28;

import "@openzeppelin/contracts/utils/cryptography/ECDSA.sol";

contract Moderator {
    struct Invoice {
        bytes32 channelId;
        uint256 nonce; 
        bytes sigL; 
        bytes sigR; 
    }

    struct Channel {
        address renter;
        address landlord;
        Invoice invoice;
        uint256 timestamp;
        uint256 expirationBlock;
        bool open;
    }

    mapping(bytes32 => Channel) public channels;
    mapping(address => bytes32) activeChannels;
    mapping(address => uint256) balances;

    event ChannelOpened(bytes32 indexed channelId, address renter, address landlord);
    event InvoiceSubmitted(bytes32 indexed channelId, uint256 nonce, uint256 expirationBlock);
    event ChannelClosed(bytes32 indexed channelId, address renter, address landlord);

    function openChannel(address renter, address landlord) external returns (bytes32) {
        require(renter != address(0) && landlord != address(0), "invalid renter or landlord.");
        require(renter != landlord, "renter and landlord can't be the same.");
        require(activeChannels[renter] == bytes32(0), "renter already has an active channel.");
        require(activeChannels[landlord] == bytes32(0), "landlord already has an active channel.");

        uint256 timestamp = block.timestamp;
        bytes32 channelId = keccak256(abi.encodePacked(renter, landlord, timestamp));
        require(channels[channelId].renter == address(0), "Channel already exists");
        
        channels[channelId] = Channel({
            renter: renter,
            landlord: landlord,
            invoice: Invoice({ channelId: bytes32(0), nonce: 0, sigL: "", sigR: "" }),
            timestamp: timestamp,
            expirationBlock: 0,
            open: true
        });

        activeChannels[renter] = channelId;
        activeChannels[landlord] = channelId;

        emit ChannelOpened(channelId, renter, landlord);
        return channelId;
    }

    function verify(bytes32 channelId, uint256 nonce, bytes memory signature, address expectedSigner) public pure returns (bool) {
        bytes32 msgHash = keccak256(abi.encodePacked(channelId, uint32(nonce)));
        bytes32 ethHash = ECDSA.toEthSignedMessageHash(msgHash);   
        address recovered = ECDSA.recover(ethHash, signature);
        return recovered == expectedSigner;
    }

    function setChannelForTest(bytes32 channelId, address renter, address landlord) public { // temporary testing function
        channels[channelId].renter = renter;
        channels[channelId].landlord = landlord;
        channels[channelId].open = true;
    }

    function submitInvoice(bytes32 channelId, uint256 nonce, bytes calldata sigL, bytes calldata sigR) external {
        Channel storage channel = channels[channelId];

        require(nonce > channel.invoice.nonce, "new invoice must have a higher nonce.");
        require(channel.open, "channel is closed.");

        bool verifyRenter = verify(channelId, nonce, sigR, channel.renter);
        bool verifyLandlord = verify(channelId, nonce, sigL, channel.landlord);

        require(verifyRenter, "renter signature cannot be verified.");
        require(verifyLandlord, "landlord signaure cannot be verified.");

        channel.invoice = Invoice({
            channelId: channelId,
            nonce: nonce,
            sigR: sigR,
            sigL: sigL
        });

        if (channel.expirationBlock == 0) {
            channel.expirationBlock = block.number + 3; // 3 block contest window
            emit InvoiceSubmitted(channelId, nonce, channel.expirationBlock);
        }
    }
}