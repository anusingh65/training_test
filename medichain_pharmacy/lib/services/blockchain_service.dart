import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import 'package:web3dart/web3dart.dart';
import '../config/app_config.dart';
import '../config/contract_config.dart';
import '../models/medicine_item.dart';
import 'wallet_service.dart';

class BlockchainService {
  late Web3Client _client;
  late DeployedContract _coreContract;
  late DeployedContract _scannerContract;
  late DeployedContract _batchContract;
  final WalletService _walletService;

  BlockchainService(this._walletService) {
    _initializeClient();
  }

  EthPrivateKey? get credentials => _walletService.credentials;

  void _initializeClient() {
    _client = Web3Client(AppConfig.rpcUrl, http.Client());

    _coreContract = DeployedContract(
      ContractAbi.fromJson(ContractConfig.coreAbi, 'PharmaChainCore'),
      EthereumAddress.fromHex(AppConfig.coreContractAddress),
    );

    _scannerContract = DeployedContract(
      ContractAbi.fromJson(ContractConfig.scannerAbi, 'PharmaChainScanner'),
      EthereumAddress.fromHex(AppConfig.scannerContractAddress),
    );

    _batchContract = DeployedContract(
      ContractAbi.fromJson(ContractConfig.batchAbi, 'PharmaChainBatch'),
      EthereumAddress.fromHex(AppConfig.batchContractAddress),
    );

    debugPrint('Blockchain client initialized');
  }

  // ── Read Operations ───────────────────────────────────────────────────────

  /// Get the on-chain role for an address.
  Future<int> getUserRole(String address) async {
      final result = await _client.call(
        contract: _coreContract,
        function: _coreContract.function('getActorRole'),
        params: [EthereumAddress.fromHex(address)],
      );
      final role = (result.first as BigInt).toInt();
      debugPrint('Role for $address : $role');
      return role;
  }

  Future<bool> isPharmacy(String address) async {
    final role = await getUserRole(address);
    return role == AppConfig.rolePharmacy;
  }

  /// Fetch a single medicine from the core contract.
  Future<MedicineItem?> getMedicine(int medicineId) async {
    try {
      final result = await _client.call(
        contract: _coreContract,
        function: _coreContract.function('medicines'),
        params: [BigInt.from(medicineId)],
      );

      final id = (result[0] as BigInt).toInt();
      if (id == 0) return null;

      return MedicineItem(
        id: id,
        batchId: (result[1] as BigInt).toInt(),
        ipfsHash: result[2] as String,
        contentHash: (result[3] as List<int>)
            .map((b) => b.toRadixString(16).padLeft(2, '0'))
            .join(),
        currentOwner: (result[4] as EthereumAddress).hex,
        status: (result[5] as BigInt).toInt(),
      );
    } catch (e) {
      debugPrint('Get medicine error: $e');
      return null;
    }
  }

  /// Check if a medicine is registered on-chain.
  Future<bool> isMedicineRegistered(int medicineId) async {
    try {
      final result = await _client.call(
        contract: _coreContract,
        function: _coreContract.function('isMedicineRegistered'),
        params: [BigInt.from(medicineId)],
      );
      return result.first as bool;
    } catch (e) {
      debugPrint('Check medicine error: $e');
      return false;
    }
  }

  /// Get custody history for a medicine.
  Future<({List<String> addresses, List<DateTime> timestamps})>
      getCustodyHistory(int medicineId) async {
    try {
      final result = await _client.call(
        contract: _coreContract,
        function: _coreContract.function('getCustodyHistory'),
        params: [BigInt.from(medicineId)],
      );

      final addresses = (result[0] as List)
          .map((addr) => (addr as EthereumAddress).hex)
          .toList();
      final timestamps = (result[1] as List)
          .map((ts) => DateTime.fromMillisecondsSinceEpoch(
              (ts as BigInt).toInt() * 1000))
          .toList();

      return (addresses: addresses, timestamps: timestamps);
    } catch (e) {
      debugPrint('Get custody history error: $e');
      return (addresses: <String>[], timestamps: <DateTime>[]);
    }
  }

  /// Get batch info.
  Future<({String batchNumber, String manufacturer, int totalUnits, int registeredUnits, bool isComplete})?>
      getBatch(int batchId) async {
    try {
      final result = await _client.call(
        contract: _batchContract,
        function: _batchContract.function('getBatch'),
        params: [BigInt.from(batchId)],
      );

      return (
        batchNumber: result[0] as String,
        manufacturer: (result[1] as EthereumAddress).hex,
        totalUnits: (result[2] as BigInt).toInt(),
        registeredUnits: (result[3] as BigInt).toInt(),
        isComplete: result[4] as bool,
      );
    } catch (e) {
      debugPrint('Get batch error: $e');
      return null;
    }
  }

  /// Get all medicine IDs in a batch.
  Future<List<int>> getBatchMedicines(int batchId) async {
    try {
      final result = await _client.call(
        contract: _batchContract,
        function: _batchContract.function('getBatchMedicines'),
        params: [BigInt.from(batchId)],
      );
      return (result.first as List)
          .map((id) => (id as BigInt).toInt())
          .toList();
    } catch (e) {
      debugPrint('Get batch medicines error: $e');
      return [];
    }
  }

  /// Get actor details (name, location, reputation).
  Future<({String name, String location, int reputation})?> getActor(
      String address) async {
    try {
      final result = await _client.call(
        contract: _coreContract,
        function: _coreContract.function('actors'),
        params: [EthereumAddress.fromHex(address)],
      );

      return (
        name: result[1] as String,
        location: result[2] as String,
        reputation: (result[4] as BigInt).toInt(),
      );
    } catch (e) {
      debugPrint('Get actor error: $e');
      return null;
    }
  }

  // ── Write Operations ──────────────────────────────────────────────────────

  /// Transfer custody of a single medicine to a new owner.
  /// This is the core "sell to customer" operation.
  Future<String> transferCustody({
    required int medicineId,
    required String toAddress,
  }) async {
    if (credentials == null) throw Exception('Not authenticated');

    final tx = Transaction.callContract(
      contract: _coreContract,
      function: _coreContract.function('transferCustody'),
      parameters: [
        BigInt.from(medicineId),
        EthereumAddress.fromHex(toAddress),
      ],
    );

    final txHash = await _walletService.sendTransaction(tx);
    debugPrint('Custody transferred: $txHash');
    return txHash;
  }

  /// Transfer custody of multiple medicines in one transaction.
  Future<String> transferBatch({
    required List<int> medicineIds,
    required String toAddress,
  }) async {
    if (credentials == null) throw Exception('Not authenticated');

    final tx = Transaction.callContract(
      contract: _coreContract,
      function: _coreContract.function('transferBatch'),
      parameters: [
        medicineIds.map((id) => BigInt.from(id)).toList(),
        EthereumAddress.fromHex(toAddress),
      ],
    );

    final txHash = await _walletService.sendTransaction(tx);
    debugPrint('Batch transferred: $txHash');
    return txHash;
  }

  /// Log a scan event (e.g., at point of sale).
  Future<String> logScan({
    required int medicineId,
    required double latitude,
    required double longitude,
    required String location,
    required String deviceId,
  }) async {
    if (credentials == null) throw Exception('Not authenticated');

    // Contract uses int256 * 1e6 for coordinates
    final latScaled = BigInt.from((latitude * 1e6).round());
    final lngScaled = BigInt.from((longitude * 1e6).round());

    final tx = Transaction.callContract(
      contract: _scannerContract,
      function: _scannerContract.function('logScan'),
      parameters: [
        BigInt.from(medicineId),
        latScaled,
        lngScaled,
        location,
        deviceId,
      ],
    );

    final txHash = await _walletService.sendTransaction(tx);
    debugPrint('Scan logged: $txHash');
    return txHash;
  }

  /// Poll until a transaction receipt appears.
  Future<TransactionReceipt?> waitForTransaction(String txHash) async {
    for (int i = 0; i < 60; i++) {
      try {
        final receipt = await _client.getTransactionReceipt(txHash);
        if (receipt != null) return receipt;
      } catch (_) {}
      await Future.delayed(const Duration(seconds: 1));
    }
    return null;
  }

  void dispose() {
    _client.dispose();
  }
}
