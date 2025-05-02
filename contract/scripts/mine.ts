import { network } from "hardhat";

async function main() {
    for (let i = 1; i <= 3; i++) {
        await network.provider.send("evm_mine");
        console.log(`Block ${i} mined`);
    }
}

main()
    .then(() => process.exit(0))
    .catch((err) => {
        console.error(err);
        process.exit(1);
    });
