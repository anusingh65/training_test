// Contract ABIs - Simplified versions with only required functions
class ContractConfig {
  // PharmaChainCore ABI (only manufacturer-relevant functions)
  static const String coreAbi = '''
  [
    {
      "inputs": [{"internalType": "uint256", "name": "_id", "type": "uint256"}, {"internalType": "uint256", "name": "_batchId", "type": "uint256"}, {"internalType": "string", "name": "_ipfsHash", "type": "string"}, {"internalType": "bytes32", "name": "_contentHash", "type": "bytes32"}],
      "name": "registerMedicine",
      "outputs": [],
      "stateMutability": "nonpayable",
      "type": "function"
    },
    {
      "inputs": [{"internalType": "address", "name": "_actor", "type": "address"}],
      "name": "getActorRole",
      "outputs": [{"internalType": "uint8", "name": "", "type": "uint8"}],
      "stateMutability": "view",
      "type": "function"
    },
    {
      "inputs": [{"internalType": "uint256", "name": "_id", "type": "uint256"}],
      "name": "isMedicineRegistered",
      "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
      "stateMutability": "view",
      "type": "function"
    },
    {
      "inputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
      "name": "medicines",
      "outputs": [
        {"internalType": "uint256", "name": "id", "type": "uint256"},
        {"internalType": "uint256", "name": "batchId", "type": "uint256"},
        {"internalType": "string", "name": "ipfsHash", "type": "string"},
        {"internalType": "bytes32", "name": "contentHash", "type": "bytes32"},
        {"internalType": "address", "name": "currentOwner", "type": "address"},
        {"internalType": "uint8", "name": "status", "type": "uint8"}
      ],
      "stateMutability": "view",
      "type": "function"
    }
  ]
  ''';

  // PharmaChainBatch ABI
  static const String batchAbi = '''
  [
    {
      "inputs": [{"internalType": "uint256", "name": "_batchId", "type": "uint256"}, {"internalType": "string", "name": "_batchNumber", "type": "string"}, {"internalType": "uint256", "name": "_totalUnits", "type": "uint256"}, {"internalType": "string", "name": "_ipfsHash", "type": "string"}, {"internalType": "bytes32", "name": "_contentHash", "type": "bytes32"}],
      "name": "createBatch",
      "outputs": [],
      "stateMutability": "nonpayable",
      "type": "function"
    },
    {
      "inputs": [{"internalType": "uint256", "name": "_batchId", "type": "uint256"}, {"internalType": "uint256", "name": "_medicineId", "type": "uint256"}, {"internalType": "string", "name": "_ipfsHash", "type": "string"}, {"internalType": "bytes32", "name": "_contentHash", "type": "bytes32"}],
      "name": "addMedicineToBatch",
      "outputs": [],
      "stateMutability": "nonpayable",
      "type": "function"
    },
    {
      "inputs": [{"internalType": "uint256", "name": "_batchId", "type": "uint256"}, {"internalType": "uint256[]", "name": "_medicineIds", "type": "uint256[]"}, {"internalType": "string[]", "name": "_ipfsHashes", "type": "string[]"}, {"internalType": "bytes32[]", "name": "_contentHashes", "type": "bytes32[]"}],
      "name": "addMedicinesToBatch",
      "outputs": [],
      "stateMutability": "nonpayable",
      "type": "function"
    },
    {
      "inputs": [{"internalType": "uint256", "name": "_batchId", "type": "uint256"}],
      "name": "completeBatch",
      "outputs": [],
      "stateMutability": "nonpayable",
      "type": "function"
    },
    {
      "inputs": [{"internalType": "uint256", "name": "_batchId", "type": "uint256"}],
      "name": "getBatch",
      "outputs": [
        {"internalType": "string", "name": "batchNumber", "type": "string"},
        {"internalType": "address", "name": "manufacturer", "type": "address"},
        {"internalType": "uint256", "name": "totalUnits", "type": "uint256"},
        {"internalType": "uint256", "name": "registeredUnits", "type": "uint256"},
        {"internalType": "bool", "name": "isComplete", "type": "bool"}
      ],
      "stateMutability": "view",
      "type": "function"
    },
    {
      "inputs": [{"internalType": "address", "name": "_manufacturer", "type": "address"}],
      "name": "getManufacturerBatches",
      "outputs": [{"internalType": "uint256[]", "name": "", "type": "uint256[]"}],
      "stateMutability": "view",
      "type": "function"
    },
    {
      "inputs": [{"internalType": "uint256", "name": "_batchId", "type": "uint256"}],
      "name": "getBatchMedicines",
      "outputs": [{"internalType": "uint256[]", "name": "", "type": "uint256[]"}],
      "stateMutability": "view",
      "type": "function"
    },
    {
      "inputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
      "name": "batches",
      "outputs": [
        {"internalType": "uint256", "name": "id", "type": "uint256"},
        {"internalType": "string", "name": "batchNumber", "type": "string"},
        {"internalType": "string", "name": "ipfsHash", "type": "string"},
        {"internalType": "bytes32", "name": "contentHash", "type": "bytes32"},
        {"internalType": "address", "name": "manufacturer", "type": "address"},
        {"internalType": "uint256", "name": "totalUnits", "type": "uint256"},
        {"internalType": "uint256", "name": "registeredUnits", "type": "uint256"},
        {"internalType": "uint256", "name": "createdAt", "type": "uint256"},
        {"internalType": "bool", "name": "isComplete", "type": "bool"}
      ],
      "stateMutability": "view",
      "type": "function"
    },
    {
      "anonymous": false,
      "inputs": [
        {"indexed": true, "internalType": "uint256", "name": "batchId", "type": "uint256"},
        {"indexed": true, "internalType": "address", "name": "manufacturer", "type": "address"},
        {"indexed": false, "internalType": "string", "name": "batchNumber", "type": "string"},
        {"indexed": false, "internalType": "uint256", "name": "totalUnits", "type": "uint256"},
        {"indexed": false, "internalType": "uint256", "name": "timestamp", "type": "uint256"}
      ],
      "name": "BatchCreated",
      "type": "event"
    }
  ]
  ''';
}
