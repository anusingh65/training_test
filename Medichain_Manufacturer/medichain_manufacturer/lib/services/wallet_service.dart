import 'dart:async';
import 'package:flutter/foundation.dart';
import 'package:walletconnect_flutter_v2/walletconnect_flutter_v2.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../config/app_config.dart';

class WalletService extends ChangeNotifier {
  Web3App? _web3App;
  SessionData? _session;
  String? _address;
  bool _isConnecting = false;
  String? _currentUri;

  String? get address => _address;
  bool get isConnected => _session != null && _address != null;
  bool get isConnecting => _isConnecting;
  SessionData? get session => _session;
  String? get currentUri => _currentUri;

  // Initialize WalletConnect
  Future<void> initialize() async {
    try {
      _web3App = await Web3App.createInstance(
        projectId: AppConfig.wcProjectId,
        metadata: PairingMetadata(
          name: AppConfig.appName,
          description: AppConfig.appDescription,
          url: 'https://medichain.example.com',
          icons: ['https://medichain.example.com/icon.png'],
        ),
      );

      // Set up event listeners
      _web3App!.onSessionConnect.subscribe(_onSessionConnect);
      _web3App!.onSessionDelete.subscribe(_onSessionDelete);

      // Try to restore previous session
      await _restoreSession();

      debugPrint('✅ WalletConnect initialized');
    } catch (e) {
      debugPrint('❌ WalletConnect initialization error: $e');
    }
  }

  // Connect wallet
  Future<void> connect() async {
    if (_isConnecting) return;

    try {
      _isConnecting = true;
      notifyListeners();

      final connectResponse = await _web3App!.connect(
        requiredNamespaces: {
          'eip155': RequiredNamespace(
            chains: ['eip155:${AppConfig.chainId}'],
            methods: [
              'eth_sendTransaction',
              'eth_signTransaction',
              'eth_sign',
              'personal_sign',
              'eth_signTypedData',
            ],
            events: ['chainChanged', 'accountsChanged'],
          ),
        },
      );

      final uri = connectResponse.uri;
      _currentUri = uri.toString();
      debugPrint('WalletConnect URI: $uri');
      debugPrint('Scan this with your wallet app');

      // Notify listeners so UI can show QR code
      notifyListeners();

      // Wait for session approval
      await connectResponse.session.future;

      debugPrint('✅ Wallet connected');
    } catch (e) {
      debugPrint('❌ Connection error: $e');
      rethrow;
    } finally {
      _isConnecting = false;
      notifyListeners();
    }
  }

  // Disconnect wallet
  Future<void> disconnect() async {
    if (_session == null) return;

    try {
      await _web3App!.disconnectSession(
        topic: _session!.topic,
        reason: const WalletConnectError(
          code: 0,
          message: 'User disconnected',
        ),
      );

      await _clearSession();
      debugPrint('✅ Wallet disconnected');
    } catch (e) {
      debugPrint('❌ Disconnect error: $e');
    }
  }

  // Send transaction
  Future<String> sendTransaction({
    required String to,
    required String data,
    String? value,
  }) async {
    if (!isConnected) throw Exception('Wallet not connected');

    try {
      final result = await _web3App!.request(
        topic: _session!.topic,
        chainId: 'eip155:${AppConfig.chainId}',
        request: SessionRequestParams(
          method: 'eth_sendTransaction',
          params: [
            {
              'from': _address,
              'to': to,
              'data': data,
              'value': value ?? '0x0',
            }
          ],
        ),
      );

      return result.toString();
    } catch (e) {
      debugPrint('❌ Transaction error: $e');
      rethrow;
    }
  }

  // Sign message
  Future<String> signMessage(String message) async {
    if (!isConnected) throw Exception('Wallet not connected');

    try {
      final result = await _web3App!.request(
        topic: _session!.topic,
        chainId: 'eip155:${AppConfig.chainId}',
        request: SessionRequestParams(
          method: 'personal_sign',
          params: [message, _address],
        ),
      );

      return result.toString();
    } catch (e) {
      debugPrint('❌ Sign message error: $e');
      rethrow;
    }
  }

  // Event handlers
  void _onSessionConnect(SessionConnect? args) {
    if (args != null) {
      _session = args.session;
      _updateAddress();
      _saveSession();
      notifyListeners();
      debugPrint('✅ Session connected: ${_session?.topic}');
    }
  }

  void _onSessionDelete(SessionDelete? args) {
    _clearSession();
    notifyListeners();
    debugPrint('✅ Session deleted');
  }

  // Update address from session
  void _updateAddress() {
    if (_session == null) return;

    final namespace = _session!.namespaces['eip155'];
    if (namespace != null && namespace.accounts.isNotEmpty) {
      final account = namespace.accounts.first;
      // Format: eip155:11155111:0x1234...
      _address = account.split(':').last;
    }
  }

  // Save session to storage
  Future<void> _saveSession() async {
    if (_session == null) return;

    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString('wc_session_topic', _session!.topic);
      await prefs.setString('wc_address', _address ?? '');
    } catch (e) {
      debugPrint('❌ Save session error: $e');
    }
  }

  // Restore previous session
  Future<void> _restoreSession() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final topic = prefs.getString('wc_session_topic');
      final address = prefs.getString('wc_address');

      if (topic != null && address != null) {
        // Check if session still exists
        final sessions = _web3App!.sessions.getAll();
        _session = sessions.firstWhere(
          (s) => s.topic == topic,
          orElse: () => throw Exception('Session not found'),
        );

        _address = address;
        notifyListeners();
        debugPrint('✅ Session restored: $topic');
      }
    } catch (e) {
      debugPrint('❌ Restore session error: $e');
      await _clearSession();
    }
  }

  // Clear session from storage
  Future<void> _clearSession() async {
    _session = null;
    _address = null;
    _currentUri = null;

    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.remove('wc_session_topic');
      await prefs.remove('wc_address');
    } catch (e) {
      debugPrint('❌ Clear session error: $e');
    }
  }

  // Clear current URI
  void clearCurrentUri() {
    _currentUri = null;
    notifyListeners();
  }

  @override
  void dispose() {
    _web3App?.onSessionConnect.unsubscribe(_onSessionConnect);
    _web3App?.onSessionDelete.unsubscribe(_onSessionDelete);
    super.dispose();
  }
}
