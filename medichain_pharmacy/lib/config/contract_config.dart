/// Contract ABIs — pharmacy-relevant functions only.
class ContractConfig {
  // PharmaChainCore ABI
  static const String coreAbi = '''
  [
    {
      "inputs": [{"internalType": "address", "name": "_actor", "type": "address"}],
      "name": "getActorRole",
      "outputs": [{"internalType": "uint8", "name": "", "type": "uint8"}],
      "stateMutability": "view",
      "type": "function"
    },
    {
      "inputs": [{"internalType": "address", "name": "", "type": "address"}],
      "name": "actors",
      "outputs": [
        {"internalType": "uint8", "name": "role", "type": "uint8"},
        {"internalType": "string", "name": "name", "type": "string"},
        {"internalType": "string", "name": "location", "type": "string"},
        {"internalType": "bool", "name": "isActive", "type": "bool"},
        {"internalType": "uint256", "name": "reputationScore", "type": "uint256"}
      ],
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
    },
    {
      "inputs": [{"internalType": "uint256", "name": "_id", "type": "uint256"}],
      "name": "isMedicineRegistered",
      "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
      "stateMutability": "view",
      "type": "function"
    },
    {
      "inputs": [
        {"internalType": "uint256", "name": "_id", "type": "uint256"},
        {"internalType": "address", "name": "_to", "type": "address"}
      ],
      "name": "transferCustody",
      "outputs": [],
      "stateMutability": "nonpayable",
      "type": "function"
    },
    {
      "inputs": [
        {"internalType": "uint256[]", "name": "_ids", "type": "uint256[]"},
        {"internalType": "address", "name": "_to", "type": "address"}
      ],
      "name": "transferBatch",
      "outputs": [],
      "stateMutability": "nonpayable",
      "type": "function"
    },
    {
      "inputs": [{"internalType": "uint256", "name": "_id", "type": "uint256"}],
      "name": "getCustodyHistory",
      "outputs": [
        {"internalType": "address[]", "name": "", "type": "address[]"},
        {"internalType": "uint256[]", "name": "", "type": "uint256[]"}
      ],
      "stateMutability": "view",
      "type": "function"
    }
  ]
  ''';

  // PharmaChainScanner ABI
  static const String scannerAbi = '''
  [
    {
      "inputs": [
        {"internalType": "uint256", "name": "_medicineId", "type": "uint256"},
        {"internalType": "int256", "name": "_latitude", "type": "int256"},
        {"internalType": "int256", "name": "_longitude", "type": "int256"},
        {"internalType": "string", "name": "_location", "type": "string"},
        {"internalType": "string", "name": "_deviceId", "type": "string"}
      ],
      "name": "logScan",
      "outputs": [],
      "stateMutability": "nonpayable",
      "type": "function"
    },
    {
      "inputs": [{"internalType": "uint256", "name": "_medicineId", "type": "uint256"}],
      "name": "getScanHistory",
      "outputs": [
        {
          "components": [
            {"internalType": "address", "name": "scanner", "type": "address"},
            {"internalType": "int256", "name": "latitude", "type": "int256"},
            {"internalType": "int256", "name": "longitude", "type": "int256"},
            {"internalType": "uint256", "name": "timestamp", "type": "uint256"},
            {"internalType": "string", "name": "location", "type": "string"},
            {"internalType": "string", "name": "deviceId", "type": "string"}
          ],
          "internalType": "struct PharmaChainScanner.ScanRecord[]",
          "name": "",
          "type": "tuple[]"
        }
      ],
      "stateMutability": "view",
      "type": "function"
    }
  ]
  ''';

  // PharmaChainBatch ABI (read-only for pharmacy)
  static const String batchAbi = '''
  [
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
      "inputs": [{"internalType": "uint256", "name": "_batchId", "type": "uint256"}],
      "name": "getBatchMedicines",
      "outputs": [{"internalType": "uint256[]", "name": "", "type": "uint256[]"}],
      "stateMutability": "view",
      "type": "function"
    }
  ]
  ''';
}
