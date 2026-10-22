import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:web3dart/web3dart.dart';
import 'package:http/http.dart' as http;
import '../config/app_config.dart';

class PrivateKeyWalletService extends ChangeNotifier {
  EthPrivateKey? _credentials;
  EthereumAddress? _address;
  Web3Client? _client;
  bool _isConnected = false;

  String? get address => _address?.hex;
  bool get isConnected => _isConnected && _address != null;
  EthPrivateKey? get credentials => _credentials;
  Web3Client? get client => _client;

  void _initializeClient() {
    _client = Web3Client(AppConfig.rpcUrl, http.Client());
  }

  Future<void> loginWithPrivateKey(String privateKey) async {
    try {
      String cleanKey = privateKey.trim();
      if (cleanKey.startsWith('0x')) {
        cleanKey = cleanKey.substring(2);
      }

      if (cleanKey.length != 64) {
        throw Exception('Invalid private key length. Must be 64 hex characters.');
      }

      _credentials = EthPrivateKey.fromHex(cleanKey);
      _address = _credentials!.address;
      _initializeClient();
      _isConnected = true;

      await _savePrivateKey(privateKey);

      notifyListeners();
      debugPrint('Logged in with address: ${_address!.hex}');
    } catch (e) {
      debugPrint('Login error: $e');
      rethrow;
    }
  }

  Future<void> logout() async {
    _credentials = null;
    _address = null;
    _isConnected = false;
    _client?.dispose();
    _client = null;

    await _clearPrivateKey();
    notifyListeners();
  }

  Future<String> sendTransaction(Transaction transaction) async {
    if (!isConnected || _credentials == null || _client == null) {
      throw Exception('Not connected');
    }

    try {
      final txHash = await _client!.sendTransaction(
        _credentials!,
        transaction,
        chainId: AppConfig.chainId,
      );
      debugPrint('Transaction sent: $txHash');
      return txHash;
    } catch (e) {
      debugPrint('Send transaction error: $e');
      rethrow;
    }
  }

  Future<bool> tryAutoLogin() async {
    try {
      final savedKey = await _loadPrivateKey();
      if (savedKey != null) {
        await loginWithPrivateKey(savedKey);
        return true;
      }
      return false;
    } catch (e) {
      debugPrint('Auto-login error: $e');
      return false;
    }
  }

  Future<void> _savePrivateKey(String privateKey) async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final encrypted = _xorEncrypt(privateKey);
      await prefs.setString('dist_encrypted_pk', encrypted);
    } catch (e) {
      debugPrint('Save private key error: $e');
    }
  }

  Future<String?> _loadPrivateKey() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final encrypted = prefs.getString('dist_encrypted_pk');
      if (encrypted != null) {
        return _xorDecrypt(encrypted);
      }
      return null;
    } catch (e) {
      debugPrint('Load private key error: $e');
      return null;
    }
  }

  Future<void> _clearPrivateKey() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.remove('dist_encrypted_pk');
    } catch (e) {
      debugPrint('Clear private key error: $e');
    }
  }

  String _xorEncrypt(String text) {
    const key = 'MEDICHAIN_DIST_KEY';
    final encrypted = List<int>.generate(
      text.length,
      (i) => text.codeUnitAt(i) ^ key.codeUnitAt(i % key.length),
    );
    return encrypted.map((e) => e.toRadixString(16).padLeft(2, '0')).join();
  }

  String _xorDecrypt(String encrypted) {
    const key = 'MEDICHAIN_DIST_KEY';
    final bytes = <int>[];
    for (int i = 0; i < encrypted.length; i += 2) {
      bytes.add(int.parse(encrypted.substring(i, i + 2), radix: 16));
    }
    final decrypted = List<int>.generate(
      bytes.length,
      (i) => bytes[i] ^ key.codeUnitAt(i % key.length),
    );
    return String.fromCharCodes(decrypted);
  }

  @override
  void dispose() {
    _client?.dispose();
    super.dispose();
  }
}
