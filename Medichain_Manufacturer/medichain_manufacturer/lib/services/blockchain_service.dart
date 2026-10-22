import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import 'package:web3dart/web3dart.dart';
import '../config/app_config.dart';
import '../config/contract_config.dart';
import '../models/batch_model.dart';
import 'private_key_wallet_service.dart';

class BlockchainService {
  late Web3Client _client;
  late DeployedContract _coreContract;
  late DeployedContract _batchContract;
  final PrivateKeyWalletService _walletService;

  BlockchainService(this._walletService) {
    _initializeClient();
  }

  // Get credentials for signing
  EthPrivateKey? get credentials => _walletService.credentials;

  void _initializeClient() {
    _client = Web3Client(
      AppConfig.rpcUrl,
      http.Client(),
    );

    // Initialize contracts
    _coreContract = DeployedContract(
      ContractAbi.fromJson(
        ContractConfig.coreAbi,
        'PharmaChainCore',
      ),
      EthereumAddress.fromHex(AppConfig.coreContractAddress),
    );

    _batchContract = DeployedContract(
      ContractAbi.fromJson(
        ContractConfig.batchAbi,
        'PharmaChainBatch',
      ),
      EthereumAddress.fromHex(AppConfig.batchContractAddress),
    );

    debugPrint('✅ Blockchain client initialized');
  }

  // Get user's role from blockchain
  Future<int> getUserRole(String address) async {
    try {
      final function = _coreContract.function('getActorRole');
      final result = await _client.call(
        contract: _coreContract,
        function: function,
        params: [EthereumAddress.fromHex(address)],
      );

      final role = result.first as BigInt;
      return role.toInt();
    } catch (e) {
      debugPrint('❌ Get user role error: $e');
      return 0; // No role
    }
  }

  // Check if user is a manufacturer
  Future<bool> isManufacturer(String address) async {
    final role = await getUserRole(address);
    return role == AppConfig.roleManufacturer;
  }

  // Create batch on blockchain
  Future<String> createBatch({
    required int batchId,
    required String batchNumber,
    required int totalUnits,
    required String ipfsHash,
    required String contentHash,
  }) async {
    try {
      if (credentials == null) {
        throw Exception('Not authenticated');
      }

      final function = _batchContract.function('createBatch');
      final contentHashBytes = hexToBytes(contentHash);

      final tx = Transaction.callContract(
        contract: _batchContract,
        function: function,
        parameters: [
          BigInt.from(batchId),
          batchNumber,
          BigInt.from(totalUnits),
          ipfsHash,
          contentHashBytes,
        ],
      );

      final txHash = await _walletService.sendTransaction(tx);

      debugPrint('✅ Batch created: $txHash');
      return txHash;
    } catch (e) {
      debugPrint('❌ Create batch error: $e');
      rethrow;
    }
  }

  // Add medicine to batch
  Future<String> addMedicineToBatch({
    required int batchId,
    required int medicineId,
    required String ipfsHash,
    required String contentHash,
  }) async {
    try {
      if (credentials == null) throw Exception('Not authenticated');

      final function = _batchContract.function('addMedicineToBatch');
      final contentHashBytes = hexToBytes(contentHash);

      final tx = Transaction.callContract(
        contract: _batchContract,
        function: function,
        parameters: [
          BigInt.from(batchId),
          BigInt.from(medicineId),
          ipfsHash,
          contentHashBytes,
        ],
      );

      final txHash = await _walletService.sendTransaction(tx);

      debugPrint('✅ Medicine added to batch: $txHash');
      return txHash;
    } catch (e) {
      debugPrint('❌ Add medicine error: $e');
      rethrow;
    }
  }

  // Bulk add medicines to batch
  Future<String> addMedicinesToBatch({
    required int batchId,
    required List<int> medicineIds,
    required List<String> ipfsHashes,
    required List<String> contentHashes,
  }) async {
    try {
      if (credentials == null) throw Exception('Not authenticated');

      if (medicineIds.length != ipfsHashes.length ||
          medicineIds.length != contentHashes.length) {
        throw Exception('Array lengths must match');
      }

      if (medicineIds.length > AppConfig.bulkRegistrationChunkSize) {
        throw Exception('Exceeds max batch size');
      }

      final function = _batchContract.function('addMedicinesToBatch');
      final contentHashesBytes =
          contentHashes.map((h) => hexToBytes(h)).toList();

      final tx = Transaction.callContract(
        contract: _batchContract,
        function: function,
        parameters: [
          BigInt.from(batchId),
          medicineIds.map((id) => BigInt.from(id)).toList(),
          ipfsHashes,
          contentHashesBytes,
        ],
      );

      final txHash = await _walletService.sendTransaction(tx);

      debugPrint('✅ Bulk medicines added: $txHash');
      return txHash;
    } catch (e) {
      debugPrint('❌ Bulk add medicines error: $e');
      rethrow;
    }
  }

  // Complete batch
  Future<String> completeBatch(int batchId) async {
    try {
      if (credentials == null) throw Exception('Not authenticated');

      final function = _batchContract.function('completeBatch');

      final tx = Transaction.callContract(
        contract: _batchContract,
        function: function,
        parameters: [BigInt.from(batchId)],
      );

      final txHash = await _walletService.sendTransaction(tx);

      debugPrint('✅ Batch completed: $txHash');
      return txHash;
    } catch (e) {
      debugPrint('❌ Complete batch error: $e');
      rethrow;
    }
  }

  // Get batch details from blockchain
  Future<BatchModel?> getBatch(int batchId) async {
    try {
      final function = _batchContract.function('batches');
      final result = await _client.call(
        contract: _batchContract,
        function: function,
        params: [BigInt.from(batchId)],
      );

      // Parse result
      final id = (result[0] as BigInt).toInt();
      if (id == 0) return null; // Batch doesn't exist

      final batchNumber = result[1] as String;
      final ipfsHash = result[2] as String;
      final manufacturer = (result[4] as EthereumAddress).hex;
      final totalUnits = (result[5] as BigInt).toInt();
      final registeredUnits = (result[6] as BigInt).toInt();
      final createdAt =
          DateTime.fromMillisecondsSinceEpoch((result[7] as BigInt).toInt() * 1000);
      final isComplete = result[8] as bool;

      // Fetch full details from IPFS (would need PinataService)
      // For now, return minimal data
      return BatchModel(
        batchId: id,
        batchNumber: batchNumber,
        totalUnits: totalUnits,
        registeredUnits: registeredUnits,
        ipfsHash: ipfsHash,
        manufacturer: manufacturer,
        createdAt: createdAt,
        isComplete: isComplete,
        // These would come from IPFS
        medicineName: '',
        composition: '',
        dosage: '',
        manufactureDate: DateTime.now(),
        expiryDate: DateTime.now(),
        manufacturerName: '',
        manufacturerLicense: '',
        manufacturerLocation: '',
      );
    } catch (e) {
      debugPrint('❌ Get batch error: $e');
      return null;
    }
  }

  // Get all batches for a manufacturer
  Future<List<int>> getManufacturerBatches(String manufacturerAddress) async {
    try {
      final function = _batchContract.function('getManufacturerBatches');
      final result = await _client.call(
        contract: _batchContract,
        function: function,
        params: [EthereumAddress.fromHex(manufacturerAddress)],
      );

      final batchIds = (result.first as List).map((id) => (id as BigInt).toInt()).toList();
      return batchIds;
    } catch (e) {
      debugPrint('❌ Get manufacturer batches error: $e');
      return [];
    }
  }

  // Get all medicine IDs in a batch
  Future<List<int>> getBatchMedicines(int batchId) async {
    try {
      final function = _batchContract.function('getBatchMedicines');
      final result = await _client.call(
        contract: _batchContract,
        function: function,
        params: [BigInt.from(batchId)],
      );

      final medicineIds =
          (result.first as List).map((id) => (id as BigInt).toInt()).toList();
      return medicineIds;
    } catch (e) {
      debugPrint('❌ Get batch medicines error: $e');
      return [];
    }
  }

  // Check if medicine is registered
  Future<bool> isMedicineRegistered(int medicineId) async {
    try {
      final function = _coreContract.function('isMedicineRegistered');
      final result = await _client.call(
        contract: _coreContract,
        function: function,
        params: [BigInt.from(medicineId)],
      );

      return result.first as bool;
    } catch (e) {
      debugPrint('❌ Check medicine error: $e');
      return false;
    }
  }

  // Wait for transaction confirmation
  Future<TransactionReceipt?> waitForTransaction(String txHash) async {
    try {
      debugPrint('⏳ Waiting for transaction: $txHash');

      // Poll for receipt
      for (int i = 0; i < 60; i++) {
        // Try for 60 seconds
        try {
          final receipt = await _client.getTransactionReceipt(txHash);
          if (receipt != null) {
            debugPrint('✅ Transaction confirmed: ${receipt.status}');
            return receipt;
          }
        } catch (e) {
          // Receipt not available yet
        }

        await Future.delayed(const Duration(seconds: 1));
      }

      debugPrint('⚠️ Transaction timeout');
      return null;
    } catch (e) {
      debugPrint('❌ Wait for transaction error: $e');
      return null;
    }
  }

  // Helper: Convert hex string to bytes
  Uint8List hexToBytes(String hex) {
    // Remove 0x prefix if present
    if (hex.startsWith('0x')) {
      hex = hex.substring(2);
    }

    // Ensure even length
    if (hex.length % 2 != 0) {
      hex = '0$hex';
    }

    // Pad to 32 bytes for bytes32
    hex = hex.padLeft(64, '0');

    return Uint8List.fromList(
      List.generate(hex.length ~/ 2, (i) {
        return int.parse(hex.substring(i * 2, i * 2 + 2), radix: 16);
      }),
    );
  }

  void dispose() {
    _client.dispose();
  }
}
