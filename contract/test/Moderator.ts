import { expect } from "chai";
import { ethers } from "hardhat";
import { time } from "@nomicfoundation/hardhat-network-helpers";

describe("Moderator", function () {
    async function deployFixture() {
        const [renter, landlord] = await ethers.getSigners();

        const Moderator = await ethers.getContractFactory("moderator");
        const contract = await Moderator.deploy();
        await contract.waitForDeployment();

        return { contract, renter, landlord };
    }
});

describe("Moderator", function () {
    it("should reject channel where renter and landlord are the same", async () => {
        const [renter] = await ethers.getSigners(); // only use one signer
        const Moderator = await ethers.getContractFactory("Moderator");
        const moderator = await Moderator.deploy();
        await moderator.waitForDeployment();

        await expect(
            moderator.connect(renter).openChannel(renter.address, renter.address)
        ).to.be.revertedWith("renter and landlord can't be the same.");
    });
});

describe("Moderator", function () {
    it("should open a channel successfully and compute the correct channelId", async () => {
        const [renter, landlord] = await ethers.getSigners();
        const Moderator = await ethers.getContractFactory("Moderator");
        const moderator = await Moderator.deploy();
        await moderator.waitForDeployment();

        await time.increase(1); // advance by 1 second to match block.timestamp

        const tx = await moderator.connect(renter).openChannel(renter.address, landlord.address);
        const receipt = await tx.wait();

        if (!receipt || !receipt.blockNumber) {
            throw new Error("Transaction receipt or block number is missing.");
        }

        const block = await ethers.provider.getBlock(receipt.blockNumber);
        if (!block) {
            throw new Error("Block not found.");
        }

        const actualTimestamp = block.timestamp;

        const expectedChannelId = ethers.solidityPackedKeccak256(
            ["address", "address", "uint256"],
            [renter.address, landlord.address, actualTimestamp]
        );

        await expect(tx)
            .to.emit(moderator, "ChannelOpened")
            .withArgs(expectedChannelId, renter.address, landlord.address);

        const channel = await moderator.channels(expectedChannelId);

        expect(channel.renter).to.equal(renter.address);
        expect(channel.landlord).to.equal(landlord.address);
        expect(channel.open).to.equal(true);
        expect(channel.timestamp).to.equal(actualTimestamp);
    });
});
