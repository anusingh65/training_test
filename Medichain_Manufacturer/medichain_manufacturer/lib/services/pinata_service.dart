import 'dart:convert';
import 'package:crypto/crypto.dart';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import '../config/app_config.dart';

class PinataService {
  final http.Client _client = http.Client();

  // Get authorization headers
  Map<String, String> _getHeaders() {
    if (AppConfig.pinataJwt.isNotEmpty &&
        AppConfig.pinataJwt != 'YOUR_PINATA_JWT_TOKEN') {
      return {
        'Authorization': 'Bearer ${AppConfig.pinataJwt}',
        'Content-Type': 'application/json',
      };
    }

    return {
      'pinata_api_key': AppConfig.pinataApiKey,
      'pinata_secret_api_key': AppConfig.pinataSecretKey,
      'Content-Type': 'application/json',
    };
  }

  // Test Pinata connection
  Future<bool> testConnection() async {
    try {
      final response = await _client.get(
        Uri.parse('${AppConfig.pinataApiUrl}/data/testAuthentication'),
        headers: _getHeaders(),
      );

      if (response.statusCode == 200) {
        debugPrint('✅ Pinata connection successful');
        return true;
      } else {
        debugPrint('❌ Pinata authentication failed: ${response.body}');
        return false;
      }
    } catch (e) {
      debugPrint('❌ Pinata connection error: $e');
      return false;
    }
  }

  // Upload JSON metadata to IPFS
  Future<String> uploadJson({
    required Map<String, dynamic> data,
    required String name,
    Map<String, String>? keyvalues,
  }) async {
    try {
      final body = jsonEncode({
        'pinataContent': data,
        'pinataMetadata': {
          'name': name,
          if (keyvalues != null) 'keyvalues': keyvalues,
        },
        'pinataOptions': {
          'cidVersion': 0, // Use CIDv0 (Qm...)
        }
      });

      final response = await _client.post(
        Uri.parse('${AppConfig.pinataApiUrl}/pinning/pinJSONToIPFS'),
        headers: _getHeaders(),
        body: body,
      );

      if (response.statusCode == 200) {
        final result = jsonDecode(response.body);
        final ipfsHash = result['IpfsHash'] as String;

        debugPrint('✅ Uploaded to IPFS: $ipfsHash');
        debugPrint('   View at: ${AppConfig.pinataGateway}/$ipfsHash');

        return ipfsHash;
      } else {
        throw Exception('Pinata upload failed: ${response.body}');
      }
    } catch (e) {
      debugPrint('❌ Upload error: $e');
      rethrow;
    }
  }

  // Upload medicine metadata
  Future<String> uploadMedicineMetadata(Map<String, dynamic> metadata) async {
    final medicineId = metadata['medicine_id'];

    return await uploadJson(
      data: metadata,
      name: 'medicine-$medicineId',
      keyvalues: {
        'medicine_id': medicineId.toString(),
        'batch_number': metadata['batch_number'] ?? '',
        'type': 'medicine_metadata',
      },
    );
  }

  // Upload batch metadata
  Future<String> uploadBatchMetadata(Map<String, dynamic> metadata) async {
    final batchId = metadata['batch_id'];

    return await uploadJson(
      data: metadata,
      name: 'batch-$batchId',
      keyvalues: {
        'batch_id': batchId.toString(),
        'batch_number': metadata['batch_number'] ?? '',
        'type': 'batch_metadata',
      },
    );
  }

  // Fetch data from IPFS
  Future<Map<String, dynamic>> fetchFromIPFS(String ipfsHash) async {
    try {
      // Remove ipfs:// prefix if present
      final cleanHash = ipfsHash
          .replaceAll('ipfs://', '')
          .replaceAll('/ipfs/', '');

      final response = await _client.get(
        Uri.parse('${AppConfig.pinataGateway}/$cleanHash'),
      ).timeout(const Duration(seconds: 30));

      if (response.statusCode == 200) {
        return jsonDecode(response.body) as Map<String, dynamic>;
      } else if (response.statusCode == 404) {
        throw Exception('IPFS content not found: $cleanHash');
      } else {
        throw Exception('IPFS fetch failed: ${response.statusCode}');
      }
    } catch (e) {
      debugPrint('❌ IPFS fetch error: $e');
      rethrow;
    }
  }

  // Fetch with fallback gateways
  Future<Map<String, dynamic>> fetchFromIPFSWithFallback(String ipfsHash) async {
    final gateways = [
      AppConfig.pinataGateway,
      'https://ipfs.io/ipfs',
      'https://cloudflare-ipfs.com/ipfs',
      'https://dweb.link/ipfs',
    ];

    final cleanHash = ipfsHash
        .replaceAll('ipfs://', '')
        .replaceAll('/ipfs/', '');

    for (final gateway in gateways) {
      try {
        final response = await _client.get(
          Uri.parse('$gateway/$cleanHash'),
        ).timeout(const Duration(seconds: 10));

        if (response.statusCode == 200) {
          debugPrint('✅ Fetched from: $gateway');
          return jsonDecode(response.body) as Map<String, dynamic>;
        }
      } catch (e) {
        debugPrint('❌ Failed: $gateway');
        continue;
      }
    }

    throw Exception('Failed to fetch from all IPFS gateways');
  }

  // Calculate SHA-256 content hash
  String calculateContentHash(Map<String, dynamic> data) {
    final jsonString = jsonEncode(data);
    final bytes = utf8.encode(jsonString);
    final digest = sha256.convert(bytes);
    return '0x${digest.toString()}';
  }

  // Verify content integrity
  Future<bool> verifyContent(String ipfsHash, String contentHash) async {
    try {
      final data = await fetchFromIPFS(ipfsHash);
      final calculatedHash = calculateContentHash(data);

      return calculatedHash.toLowerCase() == contentHash.toLowerCase();
    } catch (e) {
      debugPrint('❌ Verify content error: $e');
      return false;
    }
  }

  // Check if content exists on IPFS
  Future<bool> existsOnIPFS(String ipfsHash) async {
    try {
      final cleanHash = ipfsHash
          .replaceAll('ipfs://', '')
          .replaceAll('/ipfs/', '');

      final response = await _client.head(
        Uri.parse('${AppConfig.pinataGateway}/$cleanHash'),
      ).timeout(const Duration(seconds: 5));

      return response.statusCode == 200;
    } catch (e) {
      return false;
    }
  }

  // Unpin content from Pinata
  Future<bool> unpinFromIPFS(String ipfsHash) async {
    try {
      final response = await _client.delete(
        Uri.parse('${AppConfig.pinataApiUrl}/pinning/unpin/$ipfsHash'),
        headers: _getHeaders(),
      );

      if (response.statusCode == 200) {
        debugPrint('✅ Unpinned: $ipfsHash');
        return true;
      } else {
        debugPrint('❌ Unpin failed: ${response.body}');
        return false;
      }
    } catch (e) {
      debugPrint('❌ Unpin error: $e');
      return false;
    }
  }

  // List pinned medicines
  Future<List<Map<String, dynamic>>> listPinnedMedicines() async {
    try {
      final url = Uri.parse(
        '${AppConfig.pinataApiUrl}/data/pinList'
        '?metadata[keyvalues][type]={"value":"medicine_metadata","op":"eq"}',
      );

      final response = await _client.get(url, headers: _getHeaders());

      if (response.statusCode == 200) {
        final result = jsonDecode(response.body);
        final rows = result['rows'] as List;

        return rows.map((row) {
          return {
            'ipfsHash': row['ipfs_pin_hash'],
            'medicine_id': row['metadata']?['keyvalues']?['medicine_id'],
            'batch_number': row['metadata']?['keyvalues']?['batch_number'],
            'pinned_at': row['date_pinned'],
          };
        }).toList();
      } else {
        throw Exception('List pins failed: ${response.body}');
      }
    } catch (e) {
      debugPrint('❌ List pins error: $e');
      return [];
    }
  }

  // Get IPFS gateway URL
  String getIPFSUrl(String ipfsHash) {
    final cleanHash = ipfsHash
        .replaceAll('ipfs://', '')
        .replaceAll('/ipfs/', '');

    return '${AppConfig.pinataGateway}/$cleanHash';
  }

  void dispose() {
    _client.close();
  }
}
