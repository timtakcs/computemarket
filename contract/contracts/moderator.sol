// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.28;

contract Moderator {
    struct Channel {
        address renter;
        address landlord;
        uint256 timestamp;
        bool open;
    }

    mapping(bytes32 => Channel) public channels;
    mapping(address => uint256) balances;

    event ChannelOpened(bytes32 channelId, address renter, address landlord);
    event ChannelClosed(bytes32 channelId, address renter, address landlord);

    function openChannel(address renter, address landlord) external returns (bytes32) {
        require(renter != address(0) && landlord != address(0), "invalid renter or landlord.");
        require(renter != landlord, "renter and landlord can't be the same.");

        uint256 timestamp = block.timestamp;
        bytes32 channelId = keccak256(abi.encodePacked(renter, landlord, timestamp));
        require(channels[channelId].renter == address(0), "Channel already exists");
        
        channels[channelId] = Channel({
            renter: renter,
            landlord: landlord,
            timestamp: timestamp,
            open: true
        });

        emit ChannelOpened(channelId, renter, landlord);
        return channelId;
    }
}