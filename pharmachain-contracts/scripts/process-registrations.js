const hre = require("hardhat");
const fs = require("fs");
const readline = require("readline");
const path = require("path");

const DATA_DIR = path.join(__dirname, "../data");
const REGISTER_FILE = path.join(DATA_DIR, "register.json");
const DEPLOYED_ADDRESSES_FILE = path.join(__dirname, "../deployed-addresses.json");

const ROLE_FILES = {
  1: "manufacturers.json",
  2: "distributors.json",
  3: "pharmacies.json",
  4: "consumers.json",
  5: "regulators.json"
};

const ROLE_NAMES = {
  1: "Manufacturer",
  2: "Distributor",
  3: "Pharmacy",
  4: "Consumer",
  5: "Regulator"
};

async function main() {
  console.log("🚀 Starting Actor Registration Automation...\n");

  // 1. Check Files
  if (!fs.existsSync(DEPLOYED_ADDRESSES_FILE)) {
    console.error("❌ Error: deployed-addresses.json not found. Run deploy.js first.");
    process.exit(1);
  }
  if (!fs.existsSync(REGISTER_FILE)) {
    console.error(`❌ Error: ${REGISTER_FILE} not found.`);
    process.exit(1);
  }

  // 2. Load Data
  const { contracts } = JSON.parse(fs.readFileSync(DEPLOYED_ADDRESSES_FILE, "utf8"));
  const coreAddress = contracts.PharmaChainCore;
  let registrations = JSON.parse(fs.readFileSync(REGISTER_FILE, "utf8"));

  if (registrations.length === 0) {
    console.log("✅ No pending registrations found in register.json.");
    return;
  }

  console.log(`📋 Found ${registrations.length} pending registration(s):`);
  registrations.forEach((reg, index) => {
    console.log(`   ${index + 1}. [${ROLE_NAMES[reg.role] || "Unknown"}] ${reg.name} (${reg.location}) - ${reg.address}`);
  });

  // 3. Confirm with User
  const autoConfirm = process.env.AUTO_CONFIRM === 'true';

  if (!autoConfirm) {
    const confirmed = await askQuestion("\n❓ Do you want to process these registrations? (Y/n): ");
    if (confirmed.toLowerCase() === 'n') {
      console.log("❌ Operation cancelled.");
      process.exit(0);
    }
  } else {
    console.log("\n⏩ Auto-confirming registration due to AUTO_CONFIRM=true environment variable.");
  }

  // 4. Setup Contract
  const [deployer] = await hre.ethers.getSigners();
  const core = await hre.ethers.getContractAt("PharmaChainCore", coreAddress);
  console.log(`\n🔗 Connected to PharmaChainCore at ${coreAddress}`);
  console.log(`👤 using Admin Account: ${deployer.address}`);

  // 5. Process Loop
  let successfulRegistrations = [];
  let failedRegistrations = [];

  for (let i = 0; i < registrations.length; i++) {
    const reg = registrations[i];
    console.log(`\n🔄 Processing [${i+1}/${registrations.length}]: ${reg.name}...`);
    try {
      // Check if already registered
      const currentRole = await core.getActorRole(reg.address);
      if (currentRole != 0) {
        console.log(`   ⚠️  Already registered with role ${currentRole}. Skipping chain tx.`);
      } else {
        const tx = await core.registerActor(reg.address, reg.role, reg.name, reg.location);
        console.log(`   ⏳ Transaction sent: ${tx.hash}`);
        await tx.wait();
        console.log(`   ✅ Successfully registered on-chain.`);
      }
      
      // IMMEDIATE SAVE: Update role file and remove from register.json
      successfulRegistrations.push(reg);
      
      // 1. Append to Role File
      const fileName = ROLE_FILES[reg.role];
      if (fileName) {
        const filePath = path.join(DATA_DIR, fileName);
        let roleData = [];
        if (fs.existsSync(filePath)) {
          roleData = JSON.parse(fs.readFileSync(filePath, "utf8"));
        }
        if (!roleData.find(r => r.address.toLowerCase() === reg.address.toLowerCase())) {
            roleData.push(reg);
            fs.writeFileSync(filePath, JSON.stringify(roleData, null, 2));
            console.log(`   💾 Saved to ${fileName}`);
        }
      }

      // 2. Remove from register.json (Remaining items)
      // We filter out the current one and any previous successes
      const remaining = registrations.slice(i + 1); // Items ahead
      // We also need to keep the failed ones from this run so far
      const currentListToSave = [...failedRegistrations, ...remaining];
      fs.writeFileSync(REGISTER_FILE, JSON.stringify(currentListToSave, null, 2));

    } catch (error) {
      console.error(`   ❌ Failed to register ${reg.name}:`, error.message);
      failedRegistrations.push(reg);
      // We don't remove failed ones, they stay in valid positions if we rewrite the file? 
      // Actually, if we rewrite the whole file with "failed + remaining", it preserves them.
      // But better safety: Just read-modify-write register.json?
      // Simpler: Just don't remove if failed.
    }
  }

  console.log("\n✨ Done! Processed all items.");
  process.exit(0);
}

function askQuestion(query) {
  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout,
  });
  return new Promise((resolve) =>
    rl.question(query, (ans) => {
      rl.close();
      resolve(ans);
    })
  );
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
