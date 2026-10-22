import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import '../config/app_config.dart';
import '../models/manufacturer_model.dart';
import '../models/drug_model.dart';

class SupabaseService extends ChangeNotifier {
  final http.Client _client = http.Client();

  ManufacturerModel? _manufacturer;
  List<DrugModel> _drugs = [];
  bool _isLoading = false;
  String? _error;

  ManufacturerModel? get manufacturer => _manufacturer;
  List<DrugModel> get drugs => _drugs;
  bool get isLoading => _isLoading;
  String? get error => _error;
  bool get isLoaded => _manufacturer != null;

  bool get isDemoMode {
    return AppConfig.supabaseUrl.isEmpty ||
        AppConfig.supabaseUrl == 'YOUR_SUPABASE_URL' ||
        AppConfig.supabaseAnonKey.isEmpty ||
        AppConfig.supabaseAnonKey == 'YOUR_SUPABASE_ANON_KEY';
  }

  Map<String, String> get _headers => {
        'apikey': AppConfig.supabaseAnonKey,
        'Authorization': 'Bearer ${AppConfig.supabaseAnonKey}',
        'Content-Type': 'application/json',
        'Prefer': 'return=representation',
      };

  /// Fetch manufacturer profile + drug catalog. Called once after login.
  Future<void> fetchManufacturer(String publicKey) async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      if (isDemoMode) {
        await Future.delayed(const Duration(milliseconds: 300));
        _manufacturer = _getDummyManufacturer(publicKey);
        _drugs = _getDummyDrugs(publicKey);
      } else {
        // Fetch manufacturer from Supabase REST API
        final mfgUrl = Uri.parse(
          '${AppConfig.supabaseUrl}/rest/v1/manufacturers'
          '?public_key=eq.$publicKey'
          '&select=*',
        );
        final mfgResponse = await _client.get(mfgUrl, headers: _headers);

        if (mfgResponse.statusCode == 200) {
          final List<dynamic> rows = jsonDecode(mfgResponse.body);
          if (rows.isNotEmpty) {
            final row = rows.first as Map<String, dynamic>;
            _manufacturer = ManufacturerModel(
              address: row['public_key'] ?? publicKey,
              name: row['name'] ?? '',
              license: row['license_number'] ?? '',
              location: row['address'] ?? '',
              mobileNo: row['mobile_no'],
              gpsCoordinates: row['gps_coordinates'],
              ownerName: row['owner_name'],
            );
          } else {
            throw Exception('Manufacturer not found in database');
          }
        } else {
          throw Exception('Supabase error: ${mfgResponse.statusCode}');
        }

        // Fetch drugs catalog
        final drugsUrl = Uri.parse(
          '${AppConfig.supabaseUrl}/rest/v1/drugs'
          '?manufacturer_public_key=eq.$publicKey'
          '&select=*',
        );
        final drugsResponse =
            await _client.get(drugsUrl, headers: _headers);

        if (drugsResponse.statusCode == 200) {
          final List<dynamic> drugRows = jsonDecode(drugsResponse.body);
          _drugs = drugRows
              .map((row) => DrugModel.fromJson(row as Map<String, dynamic>))
              .toList();
        } else {
          throw Exception('Failed to fetch drugs: ${drugsResponse.statusCode}');
        }
      }

      debugPrint('✅ Loaded manufacturer: ${_manufacturer?.name}');
      debugPrint('✅ Loaded ${_drugs.length} drugs');
    } catch (e) {
      _error = e.toString();
      debugPrint('❌ SupabaseService error: $e');
    }

    _isLoading = false;
    notifyListeners();
  }

  /// Clear cached data on logout
  void clear() {
    _manufacturer = null;
    _drugs = [];
    _error = null;
    _isLoading = false;
    notifyListeners();
  }

  // ── Dummy Data ──────────────────────────────────────────────────────────

  ManufacturerModel _getDummyManufacturer(String publicKey) {
    return ManufacturerModel(
      address: publicKey,
      name: 'Cipla Limited',
      license: 'MFG-MH-001234',
      location: 'Mumbai, Maharashtra, India',
      mobileNo: '+91 9876543210',
      gpsCoordinates: '19.0760,72.8777',
      ownerName: 'Umang Vohra',
    );
  }

  List<DrugModel> _getDummyDrugs(String publicKey) {
    return [
      DrugModel(
        manufacturerPublicKey: publicKey,
        name: 'Paracetamol 500mg',
        composition: 'Paracetamol 500mg, Excipients q.s.',
        dosage: '1-2 tablets every 4-6 hours',
        pillsPerStrip: 10,
        expiryFromManufacture: 24,
      ),
      DrugModel(
        manufacturerPublicKey: publicKey,
        name: 'Amoxicillin 250mg',
        composition: 'Amoxicillin Trihydrate 250mg',
        dosage: '1 capsule every 8 hours',
        pillsPerStrip: 10,
        expiryFromManufacture: 36,
      ),
      DrugModel(
        manufacturerPublicKey: publicKey,
        name: 'Azithromycin 500mg',
        composition: 'Azithromycin Dihydrate 500mg',
        dosage: '1 tablet once daily for 3 days',
        pillsPerStrip: 3,
        expiryFromManufacture: 24,
      ),
      DrugModel(
        manufacturerPublicKey: publicKey,
        name: 'Cetirizine 10mg',
        composition: 'Cetirizine Hydrochloride 10mg',
        dosage: '1 tablet once daily',
        pillsPerStrip: 10,
        expiryFromManufacture: 36,
      ),
      DrugModel(
        manufacturerPublicKey: publicKey,
        name: 'Metformin 500mg',
        composition: 'Metformin Hydrochloride 500mg',
        dosage: '1 tablet twice daily with meals',
        pillsPerStrip: 10,
        expiryFromManufacture: 24,
      ),
    ];
  }

  @override
  void dispose() {
    _client.close();
    super.dispose();
  }
}
