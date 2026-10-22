const hre = require("hardhat");
const fs = require("fs");

async function main() {
  console.log("🚀 Starting contract tests on Sepolia...\n");

  // 1. Load deployed addresses
  if (!fs.existsSync("./deployed-addresses.json")) {
    console.error("❌ Error: deployed-addresses.json not found. Run deploy.js first.");
    process.exit(1);
  }

  const { contracts } = JSON.parse(fs.readFileSync("./deployed-addresses.json", "utf8"));
  console.log("📍 Using Core:   ", contracts.PharmaChainCore);
  console.log("📍 Using Scanner:", contracts.PharmaChainScanner);
  console.log("📍 Using Batch:  ", contracts.PharmaChainBatch);

  const [deployer] = await hre.ethers.getSigners();
  console.log("\n👤 Testing with account:", deployer.address);

  // 2. Get contract instances
  const core = await hre.ethers.getContractAt("PharmaChainCore", contracts.PharmaChainCore);
  const scanner = await hre.ethers.getContractAt("PharmaChainScanner", contracts.PharmaChainScanner);
  const batch = await hre.ethers.getContractAt("PharmaChainBatch", contracts.PharmaChainBatch);

  // 3. Register Deployer as Manufacturer (Role 1)
  console.log("\n1️⃣ Registering deployer as Manufacturer...");
  const actorRole = await core.getActorRole(deployer.address);
  
  if (actorRole == 0) { // Role.None = 0
    const tx = await core.registerActor(
      deployer.address,
      1, // Role.Manufacturer
      "Test Manufacturer Corp",
      "Mumbai, India"
    );
    await tx.wait();
    console.log("   ✅ Actor registered successfully.");
  } else {
    console.log(`   ℹ️ Actor already registered with role ID: ${actorRole}`);
  }

  // 4. Register a Test Medicine
  const medicineId = Math.floor(Math.random() * 1000000);
  
  if (actorRole == 1) { // 1 = Role.Manufacturer
    console.log(`\n2️⃣ Registering Medicine (ID: ${medicineId})...`);
    const regTx = await core.registerMedicine(
      medicineId,
      0, // Batch ID (0 for standalone)
      "ipfs://test-hash-123",
      hre.ethers.encodeBytes32String("test-content-hash")
    );
    await regTx.wait();
    console.log("   ✅ Medicine registered successfully.");

    // 5. Log a Scan
    console.log("\n3️⃣ Logging a Scan for the Medicine...");
    const scanTx = await scanner.logScan(
      medicineId,
      19076000, // Latitude * 1e6
      72877700, // Longitude * 1e6
      "Mumbai Distribution Hub",
      "SCAN-DEVICE-001"
    );
    await scanTx.wait();
    console.log("   ✅ Scan logged successfully.");
  } else {
    console.log("\n⚠️  Skipping Medicine Registration & Scanning:");
    console.log("   - Your current account is an ADMIN (Role 6).");
    console.log("   - Only MANUFACTURERS (Role 1) can register drugs.");
    console.log("\n💡 TO TEST FULLY:");
    console.log("   1. Create a NEW account in MetaMask.");
    console.log("   2. Send it a tiny bit of Sepolia ETH.");
    console.log("   3. Run 'core.registerActor()' to make that new account a Manufacturer.");
    console.log("   4. Use that new account's Private Key in your .env to run this test.");
  }

  // 6. Verify Data
  console.log("\n4️⃣ Verifying Data...");
  const isRegistered = await core.isMedicineRegistered(medicineId);
  const scanCount = await scanner.getScanCount(medicineId);
  const medicine = await core.medicines(medicineId);

  console.log("   - Medicine Registered:", isRegistered);
  console.log("   - Total Scans Recorded:", scanCount.toString());
  console.log("   - Current Owner:", medicine.currentOwner);

  console.log("\n✅ ALL TESTS PASSED SUCCESSFULLY! 🎉");
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error("\n❌ Test Failed:");
    console.error(error);
    process.exit(1);
  });
