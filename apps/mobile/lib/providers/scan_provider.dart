import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../services/scan_service.dart';
import '../models/scan_result.dart';

final scanServiceProvider = Provider<ScanService>((ref) => ScanService());

final lastScanResultProvider = StateProvider<ScanResult?>((ref) => null);
