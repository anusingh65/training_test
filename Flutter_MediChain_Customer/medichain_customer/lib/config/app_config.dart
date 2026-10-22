// lib/config/app_config.dart

class AppConfig {
  // ══════════════════════════════════════════════════════════
  // API Configuration
  // ══════════════════════════════════════════════════════════

  // Set this to true to use mock data, false to use real API
  static const bool useMockData = false;

  // Base URL for your backend API
  // Windows IP on WiFi hotspot — all phones on same hotspot can reach this
  static const String baseUrl = 'http://10.182.164.104:8000';

  // API Endpoints (matching the FastAPI backend)
  static const String verifyEndpoint = '/api/risk-score';
  static const String pathEndpoint = '/api/batch-trace';
  static const String reportEndpoint = '/api/heatmap-event';

  // Full URLs
  static String get verifyUrl => '$baseUrl$verifyEndpoint';
  static String get pathUrl => '$baseUrl$pathEndpoint';
  static String get reportUrl => '$baseUrl$reportEndpoint';

  // API Headers (add your auth tokens here when ready)
  static Map<String, String> get headers => {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    // 'Authorization': 'Bearer YOUR_API_KEY', // Uncomment when you have API key
  };

  // Timeouts
  static const Duration requestTimeout = Duration(seconds: 30);
  static const Duration connectionTimeout = Duration(seconds: 10);

  // ══════════════════════════════════════════════════════════
  // App Settings
  // ══════════════════════════════════════════════════════════

  static const int maxHistoryItems = 50;
  static const bool enableDebugLogs = true;
}