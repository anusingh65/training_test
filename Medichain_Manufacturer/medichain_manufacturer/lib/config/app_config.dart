class AppConfig {
  // Network Configuration
  static const String networkName = 'Sepolia Testnet';
  static const int chainId = 11155111;
  static const String rpcUrl = 'https://eth-sepolia.g.alchemy.com/v2/PGzZq8hP9sz-VFBVCNsW2';

  // Contract Addresses (from deployed-addresses.json)
  static const String coreContractAddress = '0x42b07481379ce4beF2aC70BC0329bD29a2E7cb8A';
  static const String scannerContractAddress = '0x710a91E26754c126C3A1b8C0E0c5b06568d85493';
  static const String batchContractAddress = '0x555d8aFe7FD29eC64D84e930b1Bf0265D1cC68A8';

  // IPFS Configuration
  static const String pinataApiUrl = 'https://api.pinata.cloud';
  static const String pinataGateway = 'https://gateway.pinata.cloud/ipfs';

  // TODO: Replace with your Pinata API credentials
  // SECURITY WARNING: In production, use environment variables or secure key storage
  static const String pinataApiKey = '9d8a8408676e2720c045';
  static const String pinataSecretKey = '9144e01634bf0c276cbbdfb6f5d3db11340dad53290273091d15e3745bde00eb';
  static const String pinataJwt = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySW5mb3JtYXRpb24iOnsiaWQiOiJjZmY0YzJkNy01OWQ3LTQ1ZmQtYTAyMi1iYzllYWYwNTFiNjgiLCJlbWFpbCI6Imhpc21hcnRib3kwOEBnbWFpbC5jb20iLCJlbWFpbF92ZXJpZmllZCI6dHJ1ZSwicGluX3BvbGljeSI6eyJyZWdpb25zIjpbeyJkZXNpcmVkUmVwbGljYXRpb25Db3VudCI6MSwiaWQiOiJGUkExIn0seyJkZXNpcmVkUmVwbGljYXRpb25Db3VudCI6MSwiaWQiOiJOWUMxIn1dLCJ2ZXJzaW9uIjoxfSwibWZhX2VuYWJsZWQiOmZhbHNlLCJzdGF0dXMiOiJBQ1RJVkUifSwiYXV0aGVudGljYXRpb25UeXBlIjoic2NvcGVkS2V5Iiwic2NvcGVkS2V5S2V5IjoiOWQ4YTg0MDg2NzZlMjcyMGMwNDUiLCJzY29wZWRLZXlTZWNyZXQiOiI5MTQ0ZTAxNjM0YmYwYzI3NmNiYmRmYjZmNWQzZGIxMTM0MGRhZDUzMjkwMjczMDkxZDE1ZTM3NDViZGUwMGViIiwiZXhwIjoxODAyNTAxMjU4fQ.6L-tpi65feYtXLkCyYUTg2yWdemR3gpZJ96hcn67Ovk';

  // Supabase Configuration
  // Set these to enable real Supabase backend; leave empty for dummy data mode
  static const String supabaseUrl = 'https://goprxhfpzkcyaoykkyya.supabase.co'; // e.g., 'https://xxxx.supabase.co'
  static const String supabaseAnonKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImdvcHJ4aGZwemtjeWFveWtreXlhIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzEwMzgyNzMsImV4cCI6MjA4NjYxNDI3M30.OuVmVcrdV29zKA5CikfBdkf4ffR7cQO2jJ3xCtS4pfs'; // e.g., 'eyJhbGci...'

  // WalletConnect Configuration
  static const String wcProjectId = 'fd939b9f038527d985d76eef2bd4e3ea'; // Get from https://cloud.walletconnect.com

  // App Configuration
  static const String appName = 'MediChain Manufacturer';
  static const String appDescription = 'Blockchain-based pharmaceutical supply chain management';

  // Role IDs (from smart contract)
  static const int roleManufacturer = 1;
  static const int roleDistributor = 2;
  static const int rolePharmacy = 3;
  static const int roleConsumer = 4;
  static const int roleRegulator = 5;
  static const int roleAdmin = 6;

  // Batch Configuration
  static const int maxBatchSize = 10000;
  static const int bulkRegistrationChunkSize = 100;
}
