class BlockchainConfig {
  static const String rpcUrl = String.fromEnvironment(
    'ALCHEMY_RPC_URL',
    defaultValue: 'https://polygon-amoy.g.alchemy.com/v2/YOUR_KEY',
  );

  static const String contractAddress = String.fromEnvironment(
    'CONTRACT_ADDRESS',
    defaultValue: '0x0000000000000000000000000000000000000000',
  );

  static const int chainId = 80002; // Polygon Amoy

  static const String apiBaseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://localhost:3000/api',
  );
}
