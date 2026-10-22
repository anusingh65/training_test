// lib/providers/scan_provider.dart

import 'dart:convert';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../models/scan_result.dart';
import '../models/path_point.dart';
import '../services/api_service.dart';

final scanHistoryProvider =
StateNotifierProvider<ScanHistoryNotifier, List<ScanResult>>((ref) {
  return ScanHistoryNotifier();
});

class ScanHistoryNotifier extends StateNotifier<List<ScanResult>> {
  ScanHistoryNotifier() : super([]) {
    _loadHistory();
  }

  // ══════════════════════════════════════════════════════════
  // LOAD & SAVE HISTORY
  // ══════════════════════════════════════════════════════════

  Future<void> _loadHistory() async {
    final prefs = await SharedPreferences.getInstance();
    final jsonString = prefs.getString('scan_history');
    if (jsonString != null && jsonString.isNotEmpty) {
      try {
        final List<dynamic> jsonList = json.decode(jsonString);
        state = jsonList
            .map((e) => ScanResult.fromJson(e as Map<String, dynamic>))
            .toList();
      } catch (e) {
        print('Error loading history: $e');
        state = [];
      }
    } else {
      state = [];
    }
  }

  Future<void> addScan(ScanResult result) async {
    state = [result, ...state]; // Add to beginning
    await _saveHistory();
  }

  Future<void> _saveHistory() async {
    final prefs = await SharedPreferences.getInstance();
    final jsonList = state.map((s) => s.toJson()).toList();
    final jsonString = json.encode(jsonList);
    await prefs.setString('scan_history', jsonString);
  }

  Future<void> clearHistory() async {
    state = [];
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove('scan_history');
  }

  // ══════════════════════════════════════════════════════════
  // VERIFY DRUG (uses ApiService)
  // ══════════════════════════════════════════════════════════

  Future<ScanResult> verifyDrug(String qrData) async {
    return await ApiService.verifyDrug(qrData);
  }

  // ══════════════════════════════════════════════════════════
  // GET SUPPLY CHAIN PATH (uses ApiService)
  // ══════════════════════════════════════════════════════════

  Future<List<PathPoint>> getSupplyChainPath(String drugId) async {
    return await ApiService.getSupplyChainPath(drugId);
  }

  // ══════════════════════════════════════════════════════════
  // REPORT SUSPICIOUS (uses ApiService)
  // ══════════════════════════════════════════════════════════

  Future<bool> reportSuspicious({
    required String drugId,
    required String reason,
    String? imagePath,
  }) async {
    return await ApiService.reportSuspicious(
      drugId: drugId,
      reason: reason,
      imagePath: imagePath,
    );
  }
}