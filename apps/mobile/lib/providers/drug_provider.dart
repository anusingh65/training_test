import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../services/drug_service.dart';
import '../services/blockchain_service.dart';

final drugServiceProvider = Provider<DrugService>((ref) => DrugService());

final blockchainServiceProvider =
    Provider<BlockchainService>((ref) => BlockchainService());
