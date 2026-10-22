import 'dart:convert';
import 'package:crypto/crypto.dart';
import 'package:http/http.dart' as http;
import '../config/blockchain_config.dart';
import '../models/scan_result.dart';

class ScanService {
  /// Parse QR payload: pharmachain://drugId|batchId|mfgDate|expiryDate|manufacturer|hash
  Map<String, String>? parseQrPayload(String raw) {
    if (!raw.startsWith('pharmachain://')) return null;

    final parts = raw.replaceFirst('pharmachain://', '').split('|');
    if (parts.length < 6) return null;

    return {
      'drugId': parts[0],
      'batchId': parts[1],
      'mfgDate': parts[2],
      'expiryDate': parts[3],
      'manufacturer': parts[4],
      'hash': parts[5],
    };
  }

  /// Compute SHA-256 hash locally
  String computeHash(String drugId, String batchId, String mfgDate,
      String expiryDate, String manufacturer) {
    final payload = '$drugId|$batchId|$mfgDate|$expiryDate|$manufacturer';
    final bytes = utf8.encode(payload);
    final digest = sha256.convert(bytes);
    return digest.toString();
  }

  /// Verify drug via API
  Future<ScanResult> verifyDrug(Map<String, String> qrData) async {
    final localHash = computeHash(
      qrData['drugId']!,
      qrData['batchId']!,
      qrData['mfgDate']!,
      qrData['expiryDate']!,
      qrData['manufacturer']!,
    );

    final hashMatch = localHash == qrData['hash'];

    // Call verify API
    try {
      final verifyRes = await http.post(
        Uri.parse('${BlockchainConfig.apiBaseUrl}/verify-hash'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'drugId': qrData['drugId'],
          'batchId': qrData['batchId'],
          'mfgDate': qrData['mfgDate'],
          'expiryDate': qrData['expiryDate'],
          'manufacturer': qrData['manufacturer'],
          'providedHash': qrData['hash'],
        }),
      );

      final verifyData = jsonDecode(verifyRes.body);

      // Call risk score API
      double riskScore = 50;
      String riskLevel = 'medium';
      List<String> factors = [];

      try {
        final riskRes = await http.post(
          Uri.parse('${BlockchainConfig.apiBaseUrl}/risk-score'),
          headers: {'Content-Type': 'application/json'},
          body: jsonEncode({
            'drug_id': qrData['drugId'],
            'hash_matched': hashMatch ? 1 : 0,
            'supply_chain_hops': 3,
            'time_since_manufacture': 30,
            'days_to_expiry': 365,
            'duplicate_scan': 0,
            'scan_velocity': 0.5,
            'geographic_distance': 50.0,
          }),
        );

        if (riskRes.statusCode == 200) {
          final riskData = jsonDecode(riskRes.body);
          riskScore = (riskData['risk_score'] as num).toDouble();
          riskLevel = riskData['risk_level'] ?? 'medium';
          factors = List<String>.from(riskData['contributing_factors'] ?? []);
        }
      } catch (_) {}

      return ScanResult(
        drugId: qrData['drugId']!,
        status: verifyData['status'] ?? 'suspicious',
        hashMatch: hashMatch && (verifyData['hashMatch'] ?? false),
        riskScore: riskScore,
        riskLevel: riskLevel,
        riskFactors: factors,
        drugInfo: verifyData['drug'],
      );
    } catch (e) {
      // Offline fallback
      return ScanResult(
        drugId: qrData['drugId']!,
        status: hashMatch ? 'suspicious' : 'counterfeit',
        hashMatch: hashMatch,
        riskScore: hashMatch ? 50 : 95,
        riskLevel: hashMatch ? 'medium' : 'critical',
        riskFactors: hashMatch
            ? ['Offline verification - partial check only']
            : ['Hash mismatch detected', 'Offline - unable to verify fully'],
      );
    }
  }
}
