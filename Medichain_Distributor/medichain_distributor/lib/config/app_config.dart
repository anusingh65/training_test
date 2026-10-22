class AppConfig {
  // Network Configuration
  static const String networkName = 'Sepolia Testnet';
  static const int chainId = 11155111;
  static const String rpcUrl = 'https://eth-sepolia.g.alchemy.com/v2/PGzZq8hP9sz-VFBVCNsW2';

  // Contract Addresses
  static const String coreContractAddress = '0x42b07481379ce4beF2aC70BC0329bD29a2E7cb8A';
  static const String scannerContractAddress = '0x710a91E26754c126C3A1b8C0E0c5b06568d85493';
  static const String batchContractAddress = '0x555d8aFe7FD29eC64D84e930b1Bf0265D1cC68A8';

  // Supabase Configuration (empty = dummy data mode)
  static const String supabaseUrl = '';
  static const String supabaseAnonKey = '';

  // App Configuration
  static const String appName = 'MediChain Distributor';
  static const String appDescription = 'Blockchain-based pharmaceutical distribution tracking';

  // Role IDs (from smart contract)
  static const int roleNone = 0;
  static const int roleManufacturer = 1;
  static const int roleDistributor = 2;
  static const int rolePharmacy = 3;
  static const int roleConsumer = 4;
  static const int roleRegulator = 5;
  static const int roleAdmin = 6;

  // Medicine Status (from smart contract State enum)
  static const int statusManufactured = 0;
  static const int statusInTransit = 1;
  static const int statusAtDistributor = 2;
  static const int statusAtPharmacy = 3;
  static const int statusDispensed = 4;
  static const int statusFlagged = 5;

  static String statusName(int status) {
    switch (status) {
      case statusManufactured: return 'Manufactured';
      case statusInTransit: return 'In Transit';
      case statusAtDistributor: return 'At Distributor';
      case statusAtPharmacy: return 'At Pharmacy';
      case statusDispensed: return 'Dispensed';
      case statusFlagged: return 'Flagged';
      default: return 'Unknown';
    }
  }

  static String roleName(int role) {
    switch (role) {
      case roleManufacturer: return 'Manufacturer';
      case roleDistributor: return 'Distributor';
      case rolePharmacy: return 'Pharmacy';
      case roleConsumer: return 'Consumer';
      case roleRegulator: return 'Regulator';
      case roleAdmin: return 'Admin';
      default: return 'Unknown';
    }
  }
}
