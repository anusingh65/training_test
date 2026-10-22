const hre = require("hardhat");
const fs = require("fs");

async function main() {
  console.log("🔍 Scanning Blockchain for Manufacturers...\n");

  // 1. Load Contract Address
  if (!fs.existsSync("./deployed-addresses.json")) {
    console.error("❌ Error: deployed-addresses.json not found.");
    process.exit(1);
  }
  const { contracts } = JSON.parse(fs.readFileSync("./deployed-addresses.json", "utf8"));
  const coreAddress = contracts.PharmaChainCore;

  // 2. Connect to Contract
  const core = await hre.ethers.getContractAt("PharmaChainCore", coreAddress);
  console.log(`🔗 Connected to Core: ${coreAddress}\n`);

  // 3. Query "ActorRegistered" Events
  // event ActorRegistered(address indexed actor, Role role, uint256 timestamp);
  // Note: 'role' is NOT indexed in the Solidity event, so we cannot filter it on-chain efficiently.
  // We must fetch all ActorRegistered events and filter in memory.
  
  const filter = core.filters.ActorRegistered();
  let allEvents = [];
  
  try {
    const currentBlock = await hre.ethers.provider.getBlockNumber();
    console.log(`Current Block Height: ${currentBlock}`);
    
    // We need to cover about 4000-5000 blocks based on deployment time (~11 hours ago)
    // Query in chunks of 2000 to be safe
    const CHUNK_SIZE = 20;
    const TOTAL_DEPTH = 10000; 
    
    for (let i = 0; i < TOTAL_DEPTH; i += CHUNK_SIZE) {
        const toBlock = currentBlock - i;
        const fromBlock = Math.max(0, toBlock - CHUNK_SIZE);
        
        console.log(`📡 Querying blocks ${fromBlock} to ${toBlock}...`);
        const chunk = await core.queryFilter(filter, fromBlock, toBlock);
        allEvents = allEvents.concat(chunk);
        
        if (fromBlock === 0) break;
    }
  } catch (err) {
    console.error("❌ Query failed:", err.message);
    if (err.data) console.error("Data:", err.data);
    return;
  }

  // Filter for Role.Manufacturer (1) in JS
  // event.args[1] is the role
  const events = allEvents.filter(e => Number(e.args[1]) === 1);

  if (events.length === 0) {
    console.log("⚠️  No manufacturers found on-chain.");
    return;
  }

  console.log(`✅ Found ${events.length} Manufacturer(s):\n`);

  // 4. Fetch Details for each
  for (const event of events) {
    const actorAddress = event.args[0];
    const timestamp = new Date(Number(event.args[2]) * 1000).toLocaleString();
    
    const actor = await core.actors(actorAddress);

    console.log(`🏭 Name:     ${actor.name}`);
    console.log(`📍 Location: ${actor.location}`);
    console.log(`🔑 Address:  ${actorAddress}`);
    console.log(`🕒 Joined:   ${timestamp}`);
    console.log(`⭐ Reputation: ${actor.reputationScore}`);
    console.log("---------------------------------------------------");
  }
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
