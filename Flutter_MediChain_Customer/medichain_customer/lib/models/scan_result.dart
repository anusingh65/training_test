//lib/models/scan_result.dart

import 'package:flutter/material.dart';


class ScanResult {
  final String drugId;
  final DateTime scannedAt;
  final int trustScore;
  final String status;
  final String? message;
  final bool isMock;
  final String? drugName;
  final String? manufacturer;
  final String? riskLevel;
  final String? recommendation;
  final Map<String, dynamic>? signals;

  ScanResult({
    required this.drugId,
    required this.scannedAt,
    required this.trustScore,
    required this.status,
    this.message,
    this.isMock = true,
    this.drugName,
    this.manufacturer,
    this.riskLevel,
    this.recommendation,
    this.signals,
  });

  Map<String, dynamic> toJson() => {
    'drugId': drugId,
    'scannedAt': scannedAt.toIso8601String(),
    'trustScore': trustScore,
    'status': status,
    'message': message,
    'isMock': isMock,
    'drugName': drugName,
    'manufacturer': manufacturer,
    'riskLevel': riskLevel,
    'recommendation': recommendation,
  };

  factory ScanResult.fromJson(Map<String, dynamic> json) {
    return ScanResult(
      drugId: json['drugId'] as String? ?? 'Unknown',
      scannedAt: DateTime.tryParse(json['scannedAt'] as String? ?? '') ?? DateTime.now(),
      trustScore: (json['trustScore'] as num?)?.toInt() ?? 0,
      status: json['status'] as String? ?? 'UNKNOWN',
      message: json['message'] as String?,
      isMock: json['isMock'] as bool? ?? true,
      drugName: json['drugName'] as String?,
      manufacturer: json['manufacturer'] as String?,
      riskLevel: json['riskLevel'] as String?,
      recommendation: json['recommendation'] as String?,
    );
  }

  Color get statusColor {
    switch (status) {
      case 'SAFE':
        return Colors.green;
      case 'WARNING':
        return Colors.orange;
      case 'AUTO-FLAG':
      case 'CRITICAL':
        return Colors.red;
      default:
        return Colors.grey;
    }
  }
}