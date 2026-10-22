const hre = require("hardhat");
const fs = require("fs");
const path = require("path");

async function main() {
  console.log("🔍 Verifying Manufacturers on Blockchain...\n");

  const DATA_DIR = path.join(__dirname, "../data");
  const MANUFACTURERS_FILE = path.join(DATA_DIR, "manufacturers.json");

  // 1. Load Contract
  if (!fs.existsSync("./deployed-addresses.json")) {
    console.error("❌ Error: deployed-addresses.json not found.");
    process.exit(1);
  }
  const { contracts } = JSON.parse(fs.readFileSync("./deployed-addresses.json", "utf8"));
  const coreAddress = contracts.PharmaChainCore;
  const core = await hre.ethers.getContractAt("PharmaChainCore", coreAddress);
  console.log(`🔗 Connected to Core: ${coreAddress}`);

  // 2. Load Local List
  if (!fs.existsSync(MANUFACTURERS_FILE)) {
    console.log("⚠️  No local manufacturers.json found.");
    return;
  }
  const manufacturers = JSON.parse(fs.readFileSync(MANUFACTURERS_FILE, "utf8"));
  console.log(`📂 Loaded ${manufacturers.length} manufacturer(s) from local file.\n`);

  // 3. Verify On-Chain
  for (const manuf of manufacturers) {
    process.stdout.write(`🔎 Checking ${manuf.name} (${manuf.address})... `);
    try {
      const role = await core.getActorRole(manuf.address);
      const actorInfo = await core.actors(manuf.address);
      
      if (role == 1n) { // Role.Manufacturer = 1
         console.log("✅ CONFIRMED");
         console.log(`   - Name: ${actorInfo.name}`);
         console.log(`   - Location: ${actorInfo.location}`);
         console.log(`   - Reputation: ${actorInfo.reputationScore}`);
      } else {
         console.log(`❌ MISMATCH (Role: ${role})`);
      }
    } catch (error) {
      console.log(`❌ ERROR: ${error.message}`);
    }
  }
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
