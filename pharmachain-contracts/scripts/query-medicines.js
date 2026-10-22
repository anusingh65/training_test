const hre = require("hardhat");
const fs = require("fs");

async function main() {
  console.log("🔍 Scanning Blockchain for Medicines...\n");

  // 1. Load Contract Address
  if (!fs.existsSync("./deployed-addresses.json")) {
    console.error("❌ Error: deployed-addresses.json not found.");
    process.exit(1);
  }
  const { contracts } = JSON.parse(fs.readFileSync("./deployed-addresses.json", "utf8"));
  const coreAddress = contracts.PharmaChainCore;

  // 2. Connect to Contract
  const core = await hre.ethers.getContractAt("PharmaChainCore", coreAddress);
  console.log(`🔗 Connected to Core: ${coreAddress}`);

  // 3. Check Total Count
  const total = await core.totalMedicines();
  console.log(`📊 Total Medicines Registered: ${total.toString()}\n`);

  if (total == 0n) {
    console.log("✅ No medicines found. The system is clean.");
    return;
  }

  // 4. If medicines exist, find them via Events
  // We use the chunked query approach to avoid RPC limits
  console.log("📋 Fetching details via events (this may take a moment)...");
  
  const filter = core.filters.MedicineRegistered();
  let allEvents = [];
  
  try {
    const currentBlock = await hre.ethers.provider.getBlockNumber();
    // Query last 10,000 blocks in chunks of 2000
    const CHUNK_SIZE = 20;
    const TOTAL_DEPTH = 10000; 
    
    for (let i = 0; i < TOTAL_DEPTH; i += CHUNK_SIZE) {
        const toBlock = currentBlock - i;
        const fromBlock = Math.max(0, toBlock - CHUNK_SIZE);
        
        // standard log
        // process.stdout.write(`   Scanning blocks ${fromBlock} -> ${toBlock}...\r`);
        const chunk = await core.queryFilter(filter, fromBlock, toBlock);
        allEvents = allEvents.concat(chunk);
        
        if (fromBlock === 0) break;
    }
    console.log(""); // Newline
  } catch (err) {
    console.error("\n❌ Event query failed:", err.message);
    console.log("⚠️  Fallback: Cannot list individual IDs without events.");
    return;
  }

  console.log(`\n✅ Found ${allEvents.length} Medicine(s):`);
  console.log("---------------------------------------------------");

  for (const event of allEvents) {
    const id = event.args[0];
    const med = await core.medicines(id);
    
    // Status Enum: 0=Manufactured, 1=InTransit, 2=AtDistributor, 3=AtPharmacy, 4=Dispensed, 5=Flagged
    const statuses = ["Manufactured", "InTransit", "AtDistributor", "AtPharmacy", "Dispensed", "Flagged"];
    
    console.log(`💊 ID:         ${med.id}`);
    console.log(`   Name:       (In IPFS: ${med.ipfsHash})`);
    console.log(`   Batch:      ${med.batchId}`);
    console.log(`   Status:     ${statuses[Number(med.status)]}`);
    console.log(`   Owner:      ${med.currentOwner}`);
    console.log("---------------------------------------------------");
  }
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
