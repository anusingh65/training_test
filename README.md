# PharmaChain Smart Contracts

## Why Split Contracts?

Ethereum has a **24KB contract size limit** (EIP-170). Our original contract was 44KB.

**Solution**: Split into 3 focused contracts:

```
┌─────────────────────────────────────────────────────────────┐
│                    PharmaChainCore                           │
│                    (Main Contract)                           │
├─────────────────────────────────────────────────────────────┤
│  • Medicine registration                                     │
│  • Custody transfers                                         │
│  • Actor management (Manufacturer, Distributor, Pharmacy)    │
│  • Drug flagging & resolution                                │
│  • Signature verification                                    │
│  • Reputation system                                         │
└─────────────────────────────────────────────────────────────┘
           │                           │
           ▼                           ▼
┌─────────────────────┐     ┌─────────────────────┐
│  PharmaChainScanner │     │  PharmaChainBatch   │
│  (AI Module)        │     │  (Batch Management) │
├─────────────────────┤     ├─────────────────────┤
│  • Scan logging     │     │  • Batch creation   │
│  • GPS tracking     │     │  • Bulk registration│
│  • Velocity alerts  │     │  • Batch completion │
│  • Device tracking  │     │  • Batch queries    │
└─────────────────────┘     └─────────────────────┘
```

## Contract Sizes (Optimized)

| Contract | Size | Status |
|----------|------|--------|
| PharmaChainCore | ~12KB | ✅ Deployable |
| PharmaChainScanner | ~6KB | ✅ Deployable |
| PharmaChainBatch | ~8KB | ✅ Deployable |

## Deployment

### 1. Install Dependencies
```bash
npm install
```

### 2. Configure Environment
Create `.env` file:
```
SEPOLIA_RPC_URL=https://sepolia.infura.io/v3/YOUR_KEY
PRIVATE_KEY=your_wallet_private_key
ETHERSCAN_API_KEY=your_etherscan_key
```

### 3. Compile
```bash
npx hardhat compile
```

### 4. Deploy to Sepolia
```bash
npx hardhat run scripts/deploy.js --network sepolia
```

### 5. Deploy to Local (for testing)
```bash
# Terminal 1: Start local node
npx hardhat node

# Terminal 2: Deploy
npx hardhat run scripts/deploy.js --network localhost
```

## Usage Flow

### 1. Register Actors (Admin)
```solidity
// Register a Manufacturer
core.registerActor(
    0x123...,           // address
    1,                  // Role.Manufacturer
    "Cipla Ltd",        // name
    "Mumbai"            // location
);

// Register a Distributor
core.registerActor(0x456..., 2, "MedPlus", "Delhi");

// Register a Pharmacy
core.registerActor(0x789..., 3, "Apollo Pharmacy", "Chennai");

// Register a Consumer
core.registerActor(0xabc..., 4, "John Doe", "Bangalore");
```

### 2. Create Batch (Manufacturer)
```solidity
batch.createBatch(
    1001,                           // batchId
    "BATCH-2024-001",               // batchNumber
    1000,                           // totalUnits
    "QmXyz...",                     // ipfsHash
    0x123...                        // contentHash
);
```

### 3. Register Medicines
```solidity
// Single medicine
core.registerMedicine(
    12345,              // medicineId (from QR)
    1001,               // batchId
    "QmAbc...",         // ipfsHash
    0x456...            // contentHash
);

// Bulk registration (batch QR scan)
core.registerMedicineBatch(
    [12345, 12346, 12347],
    1001,
    ["QmA...", "QmB...", "QmC..."],
    [0x111..., 0x222..., 0x333...]
);
```

### 4. Transfer Custody
```solidity
// Manufacturer → Distributor
core.transferCustody(12345, distributorAddress);

// Distributor → Pharmacy
core.transferCustody(12345, pharmacyAddress);

// Pharmacy → Consumer
core.transferCustody(12345, consumerAddress);
```

### 5. Log Scans (for AI)
```solidity
scanner.logScan(
    12345,              // medicineId
    19283746,           // latitude * 1e6 (19.283746°)
    72856432,           // longitude * 1e6 (72.856432°)
    "Apollo Pharmacy, Andheri",
    "DEVICE-001"
);
```

### 6. Flag Suspicious Drug (Consumer)
```solidity
core.flagDrug(
    12345,              // medicineId
    2                   // FlagSeverity.High
);
```

## Events for AI Pipeline

| Event | Contract | Purpose |
|-------|----------|---------|
| `MedicineRegistered` | Core | Track new medicines |
| `CustodyTransferred` | Core | Supply chain flow |
| `DrugFlagged` | Core | Consumer reports |
| `DrugScanned` | Scanner | Scan patterns |
| `VelocityAlert` | Scanner | Anomaly detection |
| `BatchCreated` | Batch | Batch tracking |
| `BatchCompleted` | Batch | Manufacturing complete |

## Listening to Events (Web3.js)

```javascript
const coreContract = new web3.eth.Contract(CORE_ABI, CORE_ADDRESS);
const scannerContract = new web3.eth.Contract(SCANNER_ABI, SCANNER_ADDRESS);

// Listen for scans
scannerContract.events.DrugScanned()
    .on('data', (event) => {
        console.log('Scan:', event.returnValues);
        // Send to AI pipeline
    });

// Listen for velocity alerts
scannerContract.events.VelocityAlert()
    .on('data', (event) => {
        console.log('ALERT:', event.returnValues);
        // Trigger investigation
    });

// Listen for flags
coreContract.events.DrugFlagged()
    .on('data', (event) => {
        console.log('Flag:', event.returnValues);
        // Update hotspot map
    });
```

## Gas Optimization Tips

1. **Use batch operations** when possible (`registerMedicineBatch`, `logBatchScan`)
2. **Optimizer is ON** with 200 runs (balance between deploy cost and runtime cost)
3. **Short error messages** to save gas
4. **Minimal storage** - only essential data on-chain

## Security Notes

- Admin functions are protected by `onlyAdmin` modifier
- Custody flow is enforced (Manufacturer → Distributor → Pharmacy → Consumer)
- Actors can be deactivated if compromised
- Contract can be paused in emergency
