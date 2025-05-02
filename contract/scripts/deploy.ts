import { ethers } from "hardhat";

async function main() {
    const ModeratorFactory = await ethers.getContractFactory("Moderator");
    const moderator = await ModeratorFactory.deploy();

    await moderator.waitForDeployment(); // ✅ use this instead of .deployed()

    const address = await moderator.getAddress(); // ✅ use this instead of .address

    console.log(`Moderator deployed to: ${address}`);
}

main().catch((error) => {
    console.error(error);
    process.exit(1);
});
