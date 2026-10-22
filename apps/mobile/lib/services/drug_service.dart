import 'package:supabase_flutter/supabase_flutter.dart';
import '../models/drug.dart';
import '../models/custody_event.dart';

class DrugService {
  final SupabaseClient _client = Supabase.instance.client;

  Future<Drug?> getDrug(String drugId) async {
    final data = await _client
        .from('drugs')
        .select()
        .eq('drug_id', drugId)
        .maybeSingle();

    if (data == null) return null;
    return Drug.fromJson(data);
  }

  Future<List<CustodyEvent>> getCustodyChain(String drugId) async {
    final data = await _client
        .from('custody_events')
        .select()
        .eq('drug_id', drugId)
        .order('timestamp', ascending: true);

    return (data as List).map((e) => CustodyEvent.fromJson(e)).toList();
  }

  Future<void> insertScan({
    required String drugId,
    required String result,
    double? riskScore,
    bool hashMatched = true,
    String? location,
    double? latitude,
    double? longitude,
  }) async {
    final user = _client.auth.currentUser;
    await _client.from('verification_scans').insert({
      'drug_id': drugId,
      'scanner_id': user?.id,
      'scanner_role': 'consumer',
      'result': result,
      'risk_score': riskScore,
      'hash_matched': hashMatched,
      'location': location,
      'latitude': latitude,
      'longitude': longitude,
    });
  }

  Future<void> flagDrug({
    required String drugId,
    required String reason,
    String? description,
    String? location,
    double? latitude,
    double? longitude,
  }) async {
    final user = _client.auth.currentUser;
    await _client.from('flagged_reports').insert({
      'drug_id': drugId,
      'reporter_id': user?.id,
      'reason': reason,
      'description': description,
      'severity': 'medium',
      'location': location,
      'latitude': latitude,
      'longitude': longitude,
    });
  }
}
