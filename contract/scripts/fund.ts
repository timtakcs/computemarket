import { ethers } from "hardhat";

async function main() {
    const moderatorAddress = "0x5FbDB2315678afecb367f032d93F642f64180aa3";
    const Moderator = await ethers.getContractFactory("Moderator");
    const moderator = await Moderator.attach(moderatorAddress);

    const [acct0, acct1] = await ethers.getSigners();
    const fiveEth = ethers.parseEther("5");

    console.log(`Depositing 5 ETH to ${acct0.address}`);
    await (await moderator.connect(acct0).depositTo(acct0.address, { value: fiveEth })).wait();

    console.log(`Depositing 5 ETH to ${acct1.address}`);
    await (await moderator.connect(acct1).depositTo(acct1.address, { value: fiveEth })).wait();

    const bal0 = await moderator.getBalance(acct0.address);
    const bal1 = await moderator.getBalance(acct1.address);
    console.log(`✅ Contract balance: acct0 = ${bal0} wei, acct1 = ${bal1} wei`);
}

main().catch((err) => {
    console.error(err);
    process.exit(1);
});
