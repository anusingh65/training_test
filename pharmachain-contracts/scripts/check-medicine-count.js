const hre = require("hardhat");
const fs = require("fs");

async function main() {
  // 1. Load Contract Address
  if (!fs.existsSync("./deployed-addresses.json")) {
    console.error("❌ Error: deployed-addresses.json not found.");
    process.exit(1);
  }
  const { contracts } = JSON.parse(fs.readFileSync("./deployed-addresses.json", "utf8"));
  
  // 2. Connect
  const core = await hre.ethers.getContractAt("PharmaChainCore", contracts.PharmaChainCore);
  
  // 3. Check Count
  try {
      const total = await core.totalMedicines();
      console.log(`\n📊 Total Medicines on Chain: ${total.toString()}`);
      
      if (total > 0n) {
          console.log("✅ Yes, medicines are present.");
      } else {
          console.log("Of course! No medicines have been registered yet.");
      }
  } catch (error) {
      console.error("❌ Error fetching count:", error.message);
  }
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
