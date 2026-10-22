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

  // Initialize Web3 client
  void _initializeClient() {
    _client = Web3Client(AppConfig.rpcUrl, http.Client());
  }

  // Login with private key
  Future<void> loginWithPrivateKey(String privateKey) async {
    try {
      // Remove 0x prefix if present
      String cleanKey = privateKey.trim();
      if (cleanKey.startsWith('0x')) {
        cleanKey = cleanKey.substring(2);
      }

      // Validate hex format
      if (cleanKey.length != 64) {
        throw Exception('Invalid private key length. Must be 64 hex characters.');
      }

      // Create credentials
      _credentials = EthPrivateKey.fromHex(cleanKey);
      _address = await _credentials!.extractAddress();
      _initializeClient();
      _isConnected = true;

      // Save to secure storage (encrypted)
      await _savePrivateKey(privateKey);

      notifyListeners();
      debugPrint('✅ Logged in with address: ${_address!.hex}');
    } catch (e) {
      debugPrint('❌ Login error: $e');
      rethrow;
    }
  }

  // Logout
  Future<void> logout() async {
    _credentials = null;
    _address = null;
    _isConnected = false;
    _client?.dispose();
    _client = null;

    await _clearPrivateKey();
    notifyListeners();
    debugPrint('✅ Logged out');
  }

  // Send transaction
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

      debugPrint('✅ Transaction sent: $txHash');
      return txHash;
    } catch (e) {
      debugPrint('❌ Send transaction error: $e');
      rethrow;
    }
  }

  // Sign message
  Future<Uint8List> signMessage(Uint8List message) async {
    if (!isConnected || _credentials == null) {
      throw Exception('Not connected');
    }

    try {
      final signature = await _credentials!.signPersonalMessage(message);
      debugPrint('✅ Message signed');
      return signature;
    } catch (e) {
      debugPrint('❌ Sign message error: $e');
      rethrow;
    }
  }

  // Auto-login with saved key
  Future<bool> tryAutoLogin() async {
    try {
      final savedKey = await _loadPrivateKey();
      if (savedKey != null) {
        await loginWithPrivateKey(savedKey);
        return true;
      }
      return false;
    } catch (e) {
      debugPrint('❌ Auto-login error: $e');
      return false;
    }
  }

  // Save private key (encrypted with simple XOR - for production use better encryption!)
  Future<void> _savePrivateKey(String privateKey) async {
    try {
      final prefs = await SharedPreferences.getInstance();

      // Simple XOR encryption (FOR DEMO ONLY - use proper encryption in production!)
      final encrypted = _xorEncrypt(privateKey);
      await prefs.setString('encrypted_pk', encrypted);

      debugPrint('⚠️ Private key saved (use proper encryption in production!)');
    } catch (e) {
      debugPrint('❌ Save private key error: $e');
    }
  }

  // Load private key
  Future<String?> _loadPrivateKey() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final encrypted = prefs.getString('encrypted_pk');

      if (encrypted != null) {
        return _xorDecrypt(encrypted);
      }
      return null;
    } catch (e) {
      debugPrint('❌ Load private key error: $e');
      return null;
    }
  }

  // Clear private key
  Future<void> _clearPrivateKey() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.remove('encrypted_pk');
    } catch (e) {
      debugPrint('❌ Clear private key error: $e');
    }
  }

  // Simple XOR encryption (FOR DEMO ONLY!)
  String _xorEncrypt(String text) {
    const key = 'MEDICHAIN_DEMO_KEY'; // In production, use secure key derivation
    final encrypted = List<int>.generate(
      text.length,
      (i) => text.codeUnitAt(i) ^ key.codeUnitAt(i % key.length),
    );
    return encrypted.map((e) => e.toRadixString(16).padLeft(2, '0')).join();
  }

  // Simple XOR decryption (FOR DEMO ONLY!)
  String _xorDecrypt(String encrypted) {
    const key = 'MEDICHAIN_DEMO_KEY';
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
