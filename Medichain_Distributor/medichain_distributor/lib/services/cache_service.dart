import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';

class CacheService {
  static const Duration defaultTTL = Duration(minutes: 30);
  static const int maxRecentScans = 20;

  // Get cached data with TTL check
  Future<Map<String, dynamic>?> get(String key) async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final raw = prefs.getString('cache_$key');
      if (raw == null) return null;

      final entry = jsonDecode(raw) as Map<String, dynamic>;
      final expiresAt = entry['expiresAt'] as int;

      if (DateTime.now().millisecondsSinceEpoch > expiresAt) {
        await prefs.remove('cache_$key');
        return null;
      }

      return entry['data'] as Map<String, dynamic>;
    } catch (e) {
      debugPrint('Cache get error: $e');
      return null;
    }
  }

  // Set cached data with TTL
  Future<void> set(String key, Map<String, dynamic> data, {Duration? ttl}) async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final entry = {
        'data': data,
        'expiresAt': DateTime.now().add(ttl ?? defaultTTL).millisecondsSinceEpoch,
      };
      await prefs.setString('cache_$key', jsonEncode(entry));
    } catch (e) {
      debugPrint('Cache set error: $e');
    }
  }

  // Remove cached entry
  Future<void> remove(String key) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove('cache_$key');
  }

  // Add to recent scans list
  Future<void> addRecentScan(int batchId) async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final raw = prefs.getStringList('recent_scans') ?? [];

      raw.remove(batchId.toString());
      raw.insert(0, batchId.toString());

      if (raw.length > maxRecentScans) {
        raw.removeRange(maxRecentScans, raw.length);
      }

      await prefs.setStringList('recent_scans', raw);
    } catch (e) {
      debugPrint('Add recent scan error: $e');
    }
  }

  // Get recent scan batch IDs
  Future<List<int>> getRecentScans() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final raw = prefs.getStringList('recent_scans') ?? [];
      return raw.map((s) => int.tryParse(s) ?? 0).where((id) => id > 0).toList();
    } catch (e) {
      debugPrint('Get recent scans error: $e');
      return [];
    }
  }

  // Clear all cache
  Future<void> clearAll() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final keys = prefs.getKeys().where((k) => k.startsWith('cache_'));
      for (final key in keys) {
        await prefs.remove(key);
      }
      await prefs.remove('recent_scans');
    } catch (e) {
      debugPrint('Clear cache error: $e');
    }
  }
}
