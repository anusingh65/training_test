import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import 'package:web3dart/web3dart.dart';
import '../config/app_config.dart';
import '../config/contract_config.dart';
import '../models/batch_model.dart';
import '../models/medicine_model.dart';
import '../models/custody_record_model.dart';
import 'private_key_wallet_service.dart';

class BlockchainService {
  late Web3Client _client;
  late DeployedContract _coreContract;
  late DeployedContract _batchContract;
  final PrivateKeyWalletService _walletService;

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

    _batchContract = DeployedContract(
      ContractAbi.fromJson(ContractConfig.batchAbi, 'PharmaChainBatch'),
      EthereumAddress.fromHex(AppConfig.batchContractAddress),
    );

    debugPrint('Blockchain client initialized');
  }

  // ── Read Operations ──────────────────────────────────────────────────────

  Future<int> getUserRole(String address) async {
    try {
      final function = _coreContract.function('getActorRole');
      final result = await _client.call(
        contract: _coreContract,
        function: function,
        params: [EthereumAddress.fromHex(address)],
      );
      return (result.first as BigInt).toInt();
    } catch (e) {
      debugPrint('Get user role error: $e');
      return 0;
    }
  }

  Future<bool> isDistributor(String address) async {
    final role = await getUserRole(address);
    return role == AppConfig.roleDistributor;
  }

  Future<Map<String, dynamic>?> getActorInfo(String address) async {
    try {
      final function = _coreContract.function('actors');
      final result = await _client.call(
        contract: _coreContract,
        function: function,
        params: [EthereumAddress.fromHex(address)],
      );
      return {
        'role': (result[0] as BigInt).toInt(),
        'name': result[1] as String,
        'location': result[2] as String,
        'isActive': result[3] as bool,
        'reputationScore': (result[4] as BigInt).toInt(),
      };
    } catch (e) {
      debugPrint('Get actor info error: $e');
      return null;
    }
  }

  Future<bool> isWhitelisted(String address) async {
    try {
      final function = _coreContract.function('isWhitelisted');
      final result = await _client.call(
        contract: _coreContract,
        function: function,
        params: [EthereumAddress.fromHex(address)],
      );
      return result.first as bool;
    } catch (e) {
      debugPrint('Check whitelist error: $e');
      return false;
    }
  }

  Future<MedicineModel?> getMedicine(int medicineId) async {
    try {
      final function = _coreContract.function('medicines');
      final result = await _client.call(
        contract: _coreContract,
        function: function,
        params: [BigInt.from(medicineId)],
      );

      final id = (result[0] as BigInt).toInt();
      if (id == 0) return null;

      return MedicineModel(
        id: id,
        batchId: (result[1] as BigInt).toInt(),
        ipfsHash: result[2] as String,
        contentHash: (result[3] as List<int>).map((b) => b.toRadixString(16).padLeft(2, '0')).join(),
        currentOwner: (result[4] as EthereumAddress).hex,
        manufacturer: (result[5] as EthereumAddress).hex,
        status: (result[6] as BigInt).toInt(),
        transferCount: (result[7] as BigInt).toInt(),
        scanCount: (result[8] as BigInt).toInt(),
        flagCount: (result[9] as BigInt).toInt(),
        isFlagged: result[10] as bool,
      );
    } catch (e) {
      debugPrint('Get medicine error: $e');
      return null;
    }
  }

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
      debugPrint('Check medicine error: $e');
      return false;
    }
  }

  Future<List<CustodyRecordModel>> getCustodyHistory(int medicineId) async {
    try {
      final function = _coreContract.function('getCustodyHistory');
      final result = await _client.call(
        contract: _coreContract,
        function: function,
        params: [BigInt.from(medicineId)],
      );

      final addresses = (result[0] as List).cast<EthereumAddress>();
      final timestamps = (result[1] as List).cast<BigInt>();

      final records = <CustodyRecordModel>[];
      for (int i = 0; i < addresses.length; i++) {
        records.add(CustodyRecordModel(
          address: addresses[i].hex,
          timestamp: DateTime.fromMillisecondsSinceEpoch(
            timestamps[i].toInt() * 1000,
          ),
        ));
      }
      return records;
    } catch (e) {
      debugPrint('Get custody history error: $e');
      return [];
    }
  }

  Future<BatchModel?> getBatch(int batchId) async {
    try {
      final function = _batchContract.function('batches');
      final result = await _client.call(
        contract: _batchContract,
        function: function,
        params: [BigInt.from(batchId)],
      );

      final id = (result[0] as BigInt).toInt();
      if (id == 0) return null;

      return BatchModel(
        batchId: id,
        batchNumber: result[1] as String,
        ipfsHash: result[2] as String,
        manufacturer: (result[4] as EthereumAddress).hex,
        totalUnits: (result[5] as BigInt).toInt(),
        registeredUnits: (result[6] as BigInt).toInt(),
        createdAt: DateTime.fromMillisecondsSinceEpoch(
          (result[7] as BigInt).toInt() * 1000,
        ),
        isComplete: result[8] as bool,
      );
    } catch (e) {
      debugPrint('Get batch error: $e');
      return null;
    }
  }

  Future<List<int>> getBatchMedicines(int batchId) async {
    try {
      final function = _batchContract.function('getBatchMedicines');
      final result = await _client.call(
        contract: _batchContract,
        function: function,
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

  // ── Write Operations ─────────────────────────────────────────────────────

  Future<String> transferCustody(int medicineId, String toAddress) async {
    if (credentials == null) throw Exception('Not authenticated');

    final function = _coreContract.function('transferCustody');
    final tx = Transaction.callContract(
      contract: _coreContract,
      function: function,
      parameters: [
        BigInt.from(medicineId),
        EthereumAddress.fromHex(toAddress),
      ],
    );

    return await _walletService.sendTransaction(tx);
  }

  Future<String> transferBatch(List<int> medicineIds, String toAddress) async {
    if (credentials == null) throw Exception('Not authenticated');

    final function = _coreContract.function('transferBatch');
    final tx = Transaction.callContract(
      contract: _coreContract,
      function: function,
      parameters: [
        medicineIds.map((id) => BigInt.from(id)).toList(),
        EthereumAddress.fromHex(toAddress),
      ],
    );

    return await _walletService.sendTransaction(tx);
  }

  Future<String> flagDrug(int medicineId, int severity) async {
    if (credentials == null) throw Exception('Not authenticated');

    final function = _coreContract.function('flagDrug');
    final tx = Transaction.callContract(
      contract: _coreContract,
      function: function,
      parameters: [
        BigInt.from(medicineId),
        BigInt.from(severity),
      ],
    );

    return await _walletService.sendTransaction(tx);
  }

  // ── Transaction Confirmation ──────────────────────────────────────────────

  Future<TransactionReceipt?> waitForTransaction(String txHash) async {
    try {
      for (int i = 0; i < 60; i++) {
        try {
          final receipt = await _client.getTransactionReceipt(txHash);
          if (receipt != null) return receipt;
        } catch (_) {}
        await Future.delayed(const Duration(seconds: 1));
      }
      return null;
    } catch (e) {
      debugPrint('Wait for transaction error: $e');
      return null;
    }
  }

  void dispose() {
    _client.dispose();
  }
}
