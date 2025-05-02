import { ethers } from "hardhat";

async function main() {
    const ONE_YEAR_IN_SECS = 365 * 24 * 60 * 60;
    const unlockTime = Math.floor(Date.now() / 1000) + ONE_YEAR_IN_SECS;

    const lockedAmount = ethers.parseEther("0.001");

    const Lock = await ethers.getContractFactory("Lock");
    const lock = await Lock.deploy(unlockTime, { value: lockedAmount });

    await lock.waitForDeployment();

    console.log(`✅ Contract deployed at: ${lock.target}`);
    console.log(`🔒 Unlock time: ${unlockTime}`);
}

main().catch((error) => {
    console.error(error);
    process.exitCode = 1;
});
