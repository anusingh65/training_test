const hre = require("hardhat");

async function main() {
  console.log("Deploying PharmaChain contracts...\n");

  const [deployer] = await hre.ethers.getSigners();
  console.log("Deploying with account:", deployer.address);
  console.log("Account balance:", (await deployer.provider.getBalance(deployer.address)).toString());

  // 1. Deploy Core Contract
  console.log("\n1. Deploying PharmaChainCore...");
  const Core = await hre.ethers.getContractFactory("PharmaChainCore");
  const core = await Core.deploy();
  await core.waitForDeployment();
  const coreAddress = await core.getAddress();
  console.log("   PharmaChainCore deployed to:", coreAddress);

  // 2. Deploy Scanner Contract
  console.log("\n2. Deploying PharmaChainScanner...");
  const Scanner = await hre.ethers.getContractFactory("PharmaChainScanner");
  const scanner = await Scanner.deploy(coreAddress);
  await scanner.waitForDeployment();
  const scannerAddress = await scanner.getAddress();
  console.log("   PharmaChainScanner deployed to:", scannerAddress);

  // 3. Deploy Batch Contract
  console.log("\n3. Deploying PharmaChainBatch...");
  const Batch = await hre.ethers.getContractFactory("PharmaChainBatch");
  const batch = await Batch.deploy(coreAddress);
  await batch.waitForDeployment();
  const batchAddress = await batch.getAddress();
  console.log("   PharmaChainBatch deployed to:", batchAddress);

  // Summary
  console.log("\n" + "=".repeat(50));
  console.log("DEPLOYMENT COMPLETE");
  console.log("=".repeat(50));
  console.log("\nContract Addresses:");
  console.log("  PharmaChainCore:    ", coreAddress);
  console.log("  PharmaChainScanner: ", scannerAddress);
  console.log("  PharmaChainBatch:   ", batchAddress);
  
  console.log("\nNext Steps:");
  console.log("  1. Register actors using Core.registerActor()");
  console.log("  2. Manufacturers can create batches via Batch.createBatch()");
  console.log("  3. Register medicines via Core.registerMedicine() or Batch.addMedicinesToBatch()");
  console.log("  4. Log scans via Scanner.logScan()");

  // Save addresses to file
  const fs = require("fs");
  const addresses = {
    network: hre.network.name,
    deployedAt: new Date().toISOString(),
    contracts: {
      PharmaChainCore: coreAddress,
      PharmaChainScanner: scannerAddress,
      PharmaChainBatch: batchAddress,
    },
  };
  fs.writeFileSync(
    "./deployed-addresses.json",
    JSON.stringify(addresses, null, 2)
  );
  console.log("\nAddresses saved to deployed-addresses.json");
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
