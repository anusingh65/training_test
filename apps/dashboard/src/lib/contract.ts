import { ethers } from "ethers";

const CONTRACT_ADDRESS = process.env.NEXT_PUBLIC_CONTRACT_ADDRESS || "";
const RPC_URL = process.env.NEXT_PUBLIC_ALCHEMY_RPC || "";

// Minimal ABI for read operations
const MEDICHAIN_ABI = [
  "function getDrug(string drugId) view returns (tuple(string drugId, string batchId, bytes32 metadataHash, string ipfsCid, address manufacturer, uint256 registeredAt, bool flagged))",
  "function getCustodyChain(string drugId) view returns (tuple(address from, address to, string eventType, string location, uint256 timestamp)[])",
  "function scanCount(string) view returns (uint256)",
  "function admin() view returns (address)",
  "event DrugRegistered(string indexed drugId, string batchId, address manufacturer, uint256 timestamp)",
  "event CustodyTransferred(string indexed drugId, address from, address to, string eventType, string location)",
  "event DrugFlagged(string indexed drugId, address flaggedBy, uint256 timestamp)",
  "event DrugVerified(string indexed drugId, address verifiedBy, uint256 scanNumber)",
];

let provider: ethers.JsonRpcProvider | null = null;
let contract: ethers.Contract | null = null;

export function getProvider() {
  if (!provider && RPC_URL) {
    provider = new ethers.JsonRpcProvider(RPC_URL);
  }
  return provider;
}

export function getContract() {
  if (!contract && CONTRACT_ADDRESS && RPC_URL) {
    const p = getProvider()!;
    contract = new ethers.Contract(CONTRACT_ADDRESS, MEDICHAIN_ABI, p);
  }
  return contract;
}
