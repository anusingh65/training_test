import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import 'package:web3dart/web3dart.dart';
import '../config/app_config.dart';
import '../config/contract_config.dart';
import '../models/scan_record_model.dart';
import 'private_key_wallet_service.dart';

class ScannerService {
  late Web3Client _client;
  late DeployedContract _scannerContract;
  final PrivateKeyWalletService _walletService;

  ScannerService(this._walletService) {
    _client = Web3Client(AppConfig.rpcUrl, http.Client());
    _scannerContract = DeployedContract(
      ContractAbi.fromJson(ContractConfig.scannerAbi, 'PharmaChainScanner'),
      EthereumAddress.fromHex(AppConfig.scannerContractAddress),
    );
  }

  EthPrivateKey? get credentials => _walletService.credentials;

  // Log a single scan with GPS coordinates
  Future<String> logScan({
    required int medicineId,
    required double latitude,
    required double longitude,
    required String location,
    required String deviceId,
  }) async {
    if (credentials == null) throw Exception('Not authenticated');

    final function = _scannerContract.function('logScan');
    final tx = Transaction.callContract(
      contract: _scannerContract,
      function: function,
      parameters: [
        BigInt.from(medicineId),
        BigInt.from((latitude * 1e6).round()),
        BigInt.from((longitude * 1e6).round()),
        location,
        deviceId,
      ],
    );

    return await _walletService.sendTransaction(tx);
  }

  // Log batch scan for multiple medicines
  Future<String> logBatchScan({
    required List<int> medicineIds,
    required double latitude,
    required double longitude,
    required String location,
    required String deviceId,
  }) async {
    if (credentials == null) throw Exception('Not authenticated');

    final function = _scannerContract.function('logBatchScan');
    final tx = Transaction.callContract(
      contract: _scannerContract,
      function: function,
      parameters: [
        medicineIds.map((id) => BigInt.from(id)).toList(),
        BigInt.from((latitude * 1e6).round()),
        BigInt.from((longitude * 1e6).round()),
        location,
        deviceId,
      ],
    );

    return await _walletService.sendTransaction(tx);
  }

  // Get scan history for a medicine
  Future<List<ScanRecordModel>> getScanHistory(int medicineId) async {
    try {
      final function = _scannerContract.function('getScanHistory');
      final result = await _client.call(
        contract: _scannerContract,
        function: function,
        params: [BigInt.from(medicineId)],
      );

      final records = <ScanRecordModel>[];
      final tuples = result.first as List;
      for (final tuple in tuples) {
        records.add(ScanRecordModel.fromBlockchain(tuple as List));
      }
      return records;
    } catch (e) {
      debugPrint('Get scan history error: $e');
      return [];
    }
  }

  // Get scan count for a medicine
  Future<int> getScanCount(int medicineId) async {
    try {
      final function = _scannerContract.function('getScanCount');
      final result = await _client.call(
        contract: _scannerContract,
        function: function,
        params: [BigInt.from(medicineId)],
      );
      return (result.first as BigInt).toInt();
    } catch (e) {
      debugPrint('Get scan count error: $e');
      return 0;
    }
  }

  // Get global scanner stats
  Future<Map<String, int>> getStats() async {
    try {
      final function = _scannerContract.function('getStats');
      final result = await _client.call(
        contract: _scannerContract,
        function: function,
        params: [],
      );
      return {
        'totalScans': (result[0] as BigInt).toInt(),
        'totalAlerts': (result[1] as BigInt).toInt(),
      };
    } catch (e) {
      debugPrint('Get stats error: $e');
      return {'totalScans': 0, 'totalAlerts': 0};
    }
  }

  // Get total scans for current scanner
  Future<int> getMyTotalScans(String address) async {
    try {
      final function = _scannerContract.function('scannerTotalScans');
      final result = await _client.call(
        contract: _scannerContract,
        function: function,
        params: [EthereumAddress.fromHex(address)],
      );
      return (result.first as BigInt).toInt();
    } catch (e) {
      debugPrint('Get my total scans error: $e');
      return 0;
    }
  }

  void dispose() {
    _client.dispose();
  }
}
