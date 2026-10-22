// lib/services/api_service.dart

import 'dart:convert';
import 'package:http/http.dart' as http;
import '../config/app_config.dart';
import '../models/scan_result.dart';
import '../models/path_point.dart';

class ApiService {
  // ══════════════════════════════════════════════════════════
  // VERIFY DRUG (Scan QR Code)
  // ══════════════════════════════════════════════════════════

  static Future<ScanResult> verifyDrug(String qrData) async {
    if (AppConfig.useMockData) {
      return _mockVerifyDrug(qrData);
    } else {
      return _realVerifyDrug(qrData);
    }
  }

  // Mock implementation
  static Future<ScanResult> _mockVerifyDrug(String qrData) async {
    // Simulate network delay
    await Future.delayed(const Duration(seconds: 2));

    if (AppConfig.enableDebugLogs) {
      print('🔍 Mock API: Verifying drug with QR: $qrData');
    }

    int score = 85;
    String status = 'SAFE';
    String msg = 'Clean supply chain history – verified on blockchain';

    // Simulate different scenarios based on QR data
    if (qrData.contains('fake') || qrData.length < 10) {
      score = 32;
      status = 'AUTO-FLAG';
      msg = 'High anomaly detected — possible counterfeit risk';
    } else if (qrData.contains('warn')) {
      score = 55;
      status = 'WARNING';
      msg = 'Some irregularities detected in supply chain';
    }

    return ScanResult(
      drugId: qrData,
      scannedAt: DateTime.now(),
      trustScore: score,
      status: status,
      message: msg,
      isMock: true,
    );
  }

  // Map backend risk_level to display status
  static String _mapRiskLevelToStatus(String riskLevel) {
    switch (riskLevel.toLowerCase()) {
      case 'low':
        return 'SAFE';
      case 'medium':
        return 'WARNING';
      case 'high':
        return 'AUTO-FLAG';
      case 'critical':
        return 'CRITICAL';
      default:
        return 'UNKNOWN';
    }
  }

  // Real API implementation — POST /api/risk-score
  static Future<ScanResult> _realVerifyDrug(String qrData) async {
    try {
      if (AppConfig.enableDebugLogs) {
        print('Real API: Verifying drug at ${AppConfig.verifyUrl}');
      }

      // Parse medicine_id from QR data (try int, fall back to hashCode)
      int medicineId;
      try {
        medicineId = int.parse(qrData);
      } catch (_) {
        medicineId = qrData.hashCode.abs();
      }

      final response = await http
          .post(
        Uri.parse(AppConfig.verifyUrl),
        headers: AppConfig.headers,
        body: json.encode({
          'medicine_id': medicineId,
          'drug_name': qrData,
          'auto_flag': true,
        }),
      )
          .timeout(AppConfig.requestTimeout);

      if (response.statusCode == 200) {
        final data = json.decode(response.body);

        final String riskLevel = data['risk_level'] ?? 'low';
        final String status = _mapRiskLevelToStatus(riskLevel);
        final int trustScore = (data['trust_score'] as num?)?.toInt() ?? 0;
        final String recommendation = data['recommendation'] ?? '';
        final Map<String, dynamic>? signals =
            data['signals'] is Map ? Map<String, dynamic>.from(data['signals']) : null;

        return ScanResult(
          drugId: qrData,
          scannedAt: DateTime.now(),
          trustScore: trustScore,
          status: status,
          message: recommendation,
          isMock: false,
          riskLevel: riskLevel,
          recommendation: recommendation,
          signals: signals,
        );
      } else {
        throw Exception('API returned status ${response.statusCode}');
      }
    } catch (e) {
      if (AppConfig.enableDebugLogs) {
        print('API Error: $e');
      }

      return ScanResult(
        drugId: qrData,
        scannedAt: DateTime.now(),
        trustScore: 0,
        status: 'ERROR',
        message: 'Failed to verify: ${e.toString()}',
        isMock: false,
      );
    }
  }

  // ══════════════════════════════════════════════════════════
  // GET SUPPLY CHAIN PATH
  // ══════════════════════════════════════════════════════════

  static Future<List<PathPoint>> getSupplyChainPath(String drugId) async {
    if (AppConfig.useMockData) {
      return _mockGetPath(drugId);
    } else {
      return _realGetPath(drugId);
    }
  }

  // Mock implementation
  static Future<List<PathPoint>> _mockGetPath(String drugId) async {
    await Future.delayed(const Duration(seconds: 1));

    if (AppConfig.enableDebugLogs) {
      print('🔍 Mock API: Fetching path for $drugId');
    }

    return [
      PathPoint(
        location: 'Manufacturer - Sun Pharma, Mumbai',
        timestamp: DateTime.now().subtract(const Duration(days: 5)),
        action: 'Manufactured & Registered on Blockchain',
        actor: 'Sun Pharma Ltd.',
        transactionHash: '0x1a2b3c...',
      ),
      PathPoint(
        location: 'Distributor - ABC Logistics, Delhi',
        timestamp: DateTime.now().subtract(const Duration(days: 3)),
        action: 'Transferred to Distributor',
        actor: 'ABC Logistics',
        transactionHash: '0x4d5e6f...',
      ),
      PathPoint(
        location: 'Wholesaler - XYZ Pharma, Gurugram',
        timestamp: DateTime.now().subtract(const Duration(days: 1)),
        action: 'Transferred to Wholesaler',
        actor: 'XYZ Pharma Wholesale',
        transactionHash: '0x7g8h9i...',
      ),
      PathPoint(
        location: 'Pharmacy - HealthPlus, Sector 14, Gurugram',
        timestamp: DateTime.now().subtract(const Duration(hours: 12)),
        action: 'Received at Pharmacy',
        actor: 'HealthPlus Pharmacy',
        transactionHash: '0xjklmno...',
      ),
      PathPoint(
        location: 'Your Location - Gurugram',
        timestamp: DateTime.now(),
        action: 'Scanned & Verified by Consumer',
        actor: 'You',
        transactionHash: null,
      ),
    ];
  }

  // Real API implementation — GET /api/batch-trace/{batch_id}
  static Future<List<PathPoint>> _realGetPath(String drugId) async {
    try {
      if (AppConfig.enableDebugLogs) {
        print('Real API: Fetching path from ${AppConfig.pathUrl}/$drugId');
      }

      final response = await http
          .get(
        Uri.parse('${AppConfig.pathUrl}/$drugId'),
        headers: AppConfig.headers,
      )
          .timeout(AppConfig.requestTimeout);

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        final List<dynamic> chainData = data['chain'] ?? [];
        final Map<String, dynamic> origin = data['origin'] is Map
            ? Map<String, dynamic>.from(data['origin'])
            : {};

        final List<PathPoint> points = [];

        // Add origin as first point
        if (origin.isNotEmpty) {
          points.add(PathPoint(
            location: '${origin['actor'] ?? 'Manufacturer'}, ${origin['state'] ?? ''}',
            timestamp: chainData.isNotEmpty
                ? (DateTime.tryParse(chainData[0]['timestamp'] ?? '') ??
                    DateTime.now().subtract(const Duration(days: 7)))
                : DateTime.now().subtract(const Duration(days: 7)),
            action: 'Manufactured & Registered',
            actor: origin['actor'] ?? 'Unknown Manufacturer',
          ));
        }

        // Transform chain[] into PathPoints
        for (final step in chainData) {
          final String fromActor = step['from_actor'] ?? 'Unknown';
          final String toActor = step['to_actor'] ?? 'Unknown';
          final String fromState = step['from_state'] ?? '';
          final String toState = step['to_state'] ?? '';
          final bool isAnomaly = step['is_anomaly'] == true;
          final String anomalyType = step['anomaly_type'] ?? '';

          String action = 'Transferred: $fromActor -> $toActor';
          if (isAnomaly) {
            action += ' [ANOMALY: $anomalyType]';
          }

          points.add(PathPoint(
            location: '$toActor, $toState',
            timestamp: DateTime.tryParse(step['timestamp'] ?? '') ?? DateTime.now(),
            action: action,
            actor: toActor,
          ));
        }

        // Add consumer scan as last point
        points.add(PathPoint(
          location: 'Your Location',
          timestamp: DateTime.now(),
          action: 'Scanned by Consumer',
          actor: 'You',
        ));

        return points;
      } else {
        throw Exception('API returned status ${response.statusCode}');
      }
    } catch (e) {
      if (AppConfig.enableDebugLogs) {
        print('API Error: $e');
      }
      return [];
    }
  }

  // ══════════════════════════════════════════════════════════
  // REPORT SUSPICIOUS PACKAGE
  // ══════════════════════════════════════════════════════════

  static Future<bool> reportSuspicious({
    required String drugId,
    required String reason,
    String? imagePath,
  }) async {
    if (AppConfig.useMockData) {
      return _mockReportSuspicious(drugId, reason, imagePath);
    } else {
      return _realReportSuspicious(drugId, reason, imagePath);
    }
  }

  // Mock implementation
  static Future<bool> _mockReportSuspicious(
      String drugId,
      String reason,
      String? imagePath,
      ) async {
    await Future.delayed(const Duration(seconds: 2));

    if (AppConfig.enableDebugLogs) {
      print('🔍 Mock API: Reporting $drugId');
      print('   Reason: $reason');
      print('   Image: ${imagePath ?? "None"}');
    }

    return true; // Always succeed in mock
  }

  // Real API implementation — POST /api/heatmap-event
  static Future<bool> _realReportSuspicious(
      String drugId,
      String reason,
      String? imagePath,
      ) async {
    try {
      if (AppConfig.enableDebugLogs) {
        print('Real API: Reporting to ${AppConfig.reportUrl}');
      }

      final response = await http
          .post(
        Uri.parse(AppConfig.reportUrl),
        headers: AppConfig.headers,
        body: json.encode({
          'lat': 0.0,
          'lng': 0.0,
          'flag_type': 'flagged_high',
          'label': '[$drugId] $reason',
        }),
      )
          .timeout(AppConfig.requestTimeout);

      return response.statusCode == 200 || response.statusCode == 201;
    } catch (e) {
      if (AppConfig.enableDebugLogs) {
        print('API Error: $e');
      }
      return false;
    }
  }
}