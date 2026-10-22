import 'dart:convert';
import 'package:flutter/services.dart';
import 'package:web3dart/web3dart.dart';
import 'package:http/http.dart' as http;
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import '../config/blockchain_config.dart';

class BlockchainService {
  late Web3Client _client;
  DeployedContract? _contract;
  final _storage = const FlutterSecureStorage();

  BlockchainService() {
    _client = Web3Client(BlockchainConfig.rpcUrl, http.Client());
  }

  Future<void> loadContract() async {
    final abiString = await rootBundle.loadString('assets/abi/PharmaChain.json');
    final abiJson = jsonDecode(abiString);
    final abi = jsonEncode(abiJson['abi']);

    _contract = DeployedContract(
      ContractAbi.fromJson(abi, 'PharmaChain'),
      EthereumAddress.fromHex(BlockchainConfig.contractAddress),
    );
  }

  /// Get drug info from blockchain (read-only)
  Future<Map<String, dynamic>?> getDrug(String drugId) async {
    if (_contract == null) await loadContract();

    try {
      final result = await _client.call(
        contract: _contract!,
        function: _contract!.function('getDrug'),
        params: [drugId],
      );

      if (result.isEmpty) return null;
      final drug = result[0];

      return {
        'drugId': drug[0],
        'batchId': drug[1],
        'metadataHash': drug[2],
        'ipfsCid': drug[3],
        'manufacturer': (drug[4] as EthereumAddress).hex,
        'registeredAt': (drug[5] as BigInt).toInt(),
        'flagged': drug[6] as bool,
      };
    } catch (e) {
      return null;
    }
  }

  /// Get custody chain from blockchain (read-only)
  Future<List<Map<String, dynamic>>> getCustodyChain(String drugId) async {
    if (_contract == null) await loadContract();

    try {
      final result = await _client.call(
        contract: _contract!,
        function: _contract!.function('getCustodyChain'),
        params: [drugId],
      );

      final events = result[0] as List;
      return events.map((e) => {
        return {
          'from': (e[0] as EthereumAddress).hex,
          'to': (e[1] as EthereumAddress).hex,
          'eventType': e[2] as String,
          'location': e[3] as String,
          'timestamp': (e[4] as BigInt).toInt(),
        };
      }).toList();
    } catch (e) {
      return [];
    }
  }

  /// Generate or load wallet for commuter
  Future<EthereumAddress> getOrCreateWallet() async {
    String? privateKey = await _storage.read(key: 'wallet_private_key');

    if (privateKey == null) {
      final credentials = EthPrivateKey.createRandom(Random.secure());
      privateKey = bytesToHex(credentials.privateKey);
      await _storage.write(key: 'wallet_private_key', value: privateKey);
    }

    final credentials = EthPrivateKey.fromHex(privateKey);
    return credentials.address;
  }

  /// Transfer custody (commuter tx signing)
  Future<String?> transferCustody({
    required String drugId,
    required String toAddress,
    required String eventType,
    required String location,
  }) async {
    if (_contract == null) await loadContract();

    final privateKey = await _storage.read(key: 'wallet_private_key');
    if (privateKey == null) return null;

    try {
      final credentials = EthPrivateKey.fromHex(privateKey);

      final txHash = await _client.sendTransaction(
        credentials,
        Transaction.callContract(
          contract: _contract!,
          function: _contract!.function('transferCustody'),
          parameters: [
            drugId,
            EthereumAddress.fromHex(toAddress),
            eventType,
            location,
          ],
        ),
        chainId: BlockchainConfig.chainId,
      );

      return txHash;
    } catch (e) {
      return null;
    }
  }
}

String bytesToHex(List<int> bytes) {
  return bytes.map((b) => b.toRadixString(16).padLeft(2, '0')).join();
}
