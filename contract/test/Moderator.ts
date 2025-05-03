import { expect } from "chai";
import { ethers } from "hardhat";
import { time } from "@nomicfoundation/hardhat-network-helpers";

const invoice = {
    nonce: 1,
    channel_id:
        "112554834915606360840638919269075447075414307073622370445738349656695311434682",
    sigL:
        "0x44619c96799fda4e8e5afb07b5329afe56cc3fd3590540283178467af1ca1e565d9a5e5f19cecfdd02446fbbf970f19517ec5f2872d49403d608567faf3eac021b",
    sigR:
        "0x44619c96799fda4e8e5afb07b5329afe56cc3fd3590540283178467af1ca1e565d9a5e5f19cecfdd02446fbbf970f19517ec5f2872d49403d608567faf3eac021b"
};

describe("Moderator", function () {
    async function deployFixture() {
        const [renter, landlord, otherLandlord] = await ethers.getSigners();
        const Moderator = await ethers.getContractFactory("Moderator");
        const contract = await Moderator.deploy();
        await contract.waitForDeployment();
        return { contract, renter, landlord, otherLandlord };
    }

    it("should reject channel where renter and landlord are the same", async () => {
        const { contract, renter } = await deployFixture();

        await expect(
            contract.connect(renter).openChannel(renter.address, renter.address)
        ).to.be.revertedWith("renter and landlord can't be the same.");
    });

    it("should open a channel successfully and compute the correct channelId", async () => {
        const { contract, renter, landlord } = await deployFixture();

        await time.increase(1);

        const tx = await contract.connect(renter).openChannel(renter.address, landlord.address);
        const receipt = await tx.wait();

        if (!receipt || !receipt.blockNumber) {
            throw new Error("Transaction receipt or block number is missing.");
        }

        const block = await ethers.provider.getBlock(receipt.blockNumber!);
        const timestamp = block!.timestamp;

        const expectedChannelId = ethers.solidityPackedKeccak256(
            ["address", "address", "uint256"],
            [renter.address, landlord.address, timestamp]
        );

        await expect(tx)
            .to.emit(contract, "ChannelOpened")
            .withArgs(expectedChannelId, renter.address, landlord.address);

        const channel = await contract.channels(expectedChannelId);
        expect(channel.renter).to.equal(renter.address);
        expect(channel.landlord).to.equal(landlord.address);
        expect(channel.open).to.be.true;
        expect(channel.timestamp).to.equal(timestamp);
    });

    it("should reject opening a second channel for the same renter or landlord", async () => {
        const { contract, renter, landlord, otherLandlord } = await deployFixture();

        await contract.openChannel(renter.address, landlord.address);

        await expect(
            contract.openChannel(renter.address, otherLandlord.address)
        ).to.be.revertedWith("renter already has an active channel.");

        await expect(
            contract.openChannel(otherLandlord.address, landlord.address)
        ).to.be.revertedWith("landlord already has an active channel.");
    });

    it("should verify a valid signature from both renter and landlord", async () => {
        const { contract } = await deployFixture();

        const channelId = ethers.zeroPadValue(ethers.toBeHex(1), 32); // channel_id = 1 as bytes32
        const nonce = 1;

        const sigL = "0x3487e0575ce0c0a7e0394fa5b057fd445289b6da1d866f8ca3145db463ead2c32ff339451c3cdf6aa31e874bc48876f65c2aff8a2c8bd0a6deaa3296ee8e187a1c";
        const sigR = "0x83848e5ff4b697d36bc8157f77b4655353b1c09ad98111a8ee68fd013a05f2b74207611b295fc68bb3fc64a403f571307a52888c782fa01a6acf2a105ff02f181b";

        const renterAddress = "0xada6710E3951ee357825baBB84cE06300B13c073";

        const validRenterSig = await contract.verify(channelId, nonce, sigR, renterAddress);
        const invalidLandlordSig = await contract.verify(channelId, nonce, sigL, renterAddress);

        expect(validRenterSig).to.be.true;
        expect(invalidLandlordSig).to.be.false;
    });

    it("should accept a valid invoice and emit an event", async () => {
        const { contract } = await deployFixture();

        const channelId = ethers.zeroPadValue(ethers.toBeHex(1), 32);
        const nonce = 1;

        const sigL =
            "0x3487e0575ce0c0a7e0394fa5b057fd445289b6da1d866f8ca3145db463ead2c32ff339451c3cdf6aa31e874bc48876f65c2aff8a2c8bd0a6deaa3296ee8e187a1c";
        const sigR =
            "0x83848e5ff4b697d36bc8157f77b4655353b1c09ad98111a8ee68fd013a05f2b74207611b295fc68bb3fc64a403f571307a52888c782fa01a6acf2a105ff02f181b";

        const renterAddr = "0xada6710E3951ee357825baBB84cE06300B13c073";
        const landlordAddr = "0x939d31bD382a5B0D536ff45E7d086321738867a2";

        await contract.setChannelForTest(channelId, renterAddr, landlordAddr); // helper required in contract

        const tx = await contract.submitInvoice(channelId, nonce, sigL, sigR);
        const receipt = await tx.wait();

        const stored = await contract.channels(channelId);
        expect(stored.invoice.nonce).to.equal(nonce);
        expect(stored.invoice.sigL).to.equal(sigL);
        expect(stored.invoice.sigR).to.equal(sigR);
        expect(stored.expirationBlock).to.be.gt(0);

        await expect(tx)
            .to.emit(contract, "InvoiceSubmitted")
            .withArgs(channelId, nonce, stored.expirationBlock);
    });

    describe("Moderator.verify() with supplied invoice", () => {
        it("recovers the correct addresses and verifies both sigs", async () => {
            const Moderator = await ethers.getContractFactory("Moderator");
            const moderator = await Moderator.deploy();
            await moderator.waitForDeployment();

            const channelId = ethers.zeroPadValue(
                ethers.toBeHex(invoice.channel_id),
                32
            );

            const nonce = invoice.nonce;

            const packedHash = ethers.solidityPackedKeccak256(
                ["bytes32", "uint32"],
                [channelId, nonce]
            );
            const ethHash = ethers.hashMessage(ethers.getBytes(packedHash));

            const landlordAddr = ethers.recoverAddress(ethHash, invoice.sigL);
            const renterAddr = ethers.recoverAddress(ethHash, invoice.sigR);

            console.log(" landlordAddr:", landlordAddr);
            console.log(" renterAddr  :", renterAddr);

            const landlordOk = await moderator.verify(
                channelId,
                nonce,
                invoice.sigL,
                landlordAddr
            );
            const renterOk = await moderator.verify(
                channelId,
                nonce,
                invoice.sigR,
                renterAddr
            );

            expect(landlordOk).to.be.true;
            expect(renterOk).to.be.true;
        });
    });

    it("should reflect correct renter balance after deposit", async () => {
        const { contract, renter } = await deployFixture();

        const depositAmount = 10n;
        await contract.connect(renter).deposit({ value: depositAmount });

        const balance = await contract.getBalance(renter.address);
        expect(balance).to.equal(depositAmount);
    });

    it("should close the channel and transfer funds correctly", async () => {
        const [renter, landlord] = await ethers.getSigners();
        const Moderator = await ethers.getContractFactory("Moderator");
        const contract = await Moderator.deploy();
        await contract.waitForDeployment();

        const channelId = ethers.zeroPadValue(ethers.toBeHex(1), 32);
        const nonce = 1;

        const sigL =
            "0x3487e0575ce0c0a7e0394fa5b057fd445289b6da1d866f8ca3145db463ead2c32ff339451c3cdf6aa31e874bc48876f65c2aff8a2c8bd0a6deaa3296ee8e187a1c";
        const sigR =
            "0x83848e5ff4b697d36bc8157f77b4655353b1c09ad98111a8ee68fd013a05f2b74207611b295fc68bb3fc64a403f571307a52888c782fa01a6acf2a105ff02f181b";

        const renterAddr = "0xada6710E3951ee357825baBB84cE06300B13c073";
        const landlordAddr = "0x939d31bD382a5B0D536ff45E7d086321738867a2";

        await contract.depositTo(renterAddr, { value: 10n }); // use overloaded deposit

        await contract.setChannelForTest(channelId, renterAddr, landlordAddr);
        await contract.submitInvoice(channelId, nonce, sigL, sigR);

        for (let i = 0; i < 3; i++) {
            await ethers.provider.send("evm_mine", []);
        }

        const tx = await contract.closeChannel(channelId);
        const receipt = await tx.wait();

        expect(await contract.getBalance(renterAddr)).to.equal(9n);
        expect(await contract.getBalance(landlordAddr)).to.equal(1n);

        const stored = await contract.channels(channelId);
        expect(stored.open).to.equal(false);

        await expect(tx)
            .to.emit(contract, "ChannelClosed")
            .withArgs(channelId, renterAddr, landlordAddr);
    });
});
