import 'package:flutter/foundation.dart';
import '../models/distributor_model.dart';

class SupabaseService extends ChangeNotifier {
  DistributorModel? _distributor;

  DistributorModel? get distributor => _distributor;

  bool get isDemoMode => true; // Always demo mode for now

  Future<void> fetchDistributor(String publicKey) async {
    // Demo mode: return dummy data
    _distributor = _getDummyDistributor(publicKey);
    notifyListeners();
    debugPrint('Loaded distributor profile (demo): ${_distributor!.name}');
  }

  DistributorModel _getDummyDistributor(String publicKey) {
    // Known distributor keys with dummy profiles
    final profiles = {
      '0x70B2f4452cDcBd8C3126FEc29Fd3b1B23d0D7d00'.toLowerCase(): DistributorModel(
        address: '0x70B2f4452cDcBd8C3126FEc29Fd3b1B23d0D7d00',
        name: 'MedPharma Distributors Pvt Ltd',
        license: 'DIST-MH-005678',
        location: 'Pune, Maharashtra, India',
        mobileNo: '+91 9988776655',
        gpsCoordinates: '18.5204,73.8567',
        ownerName: 'Rajesh Sharma',
        reputationScore: 500,
      ),
    };

    return profiles[publicKey.toLowerCase()] ?? DistributorModel(
      address: publicKey,
      name: 'MediChain Distributor',
      license: 'DIST-XX-000000',
      location: 'India',
      mobileNo: '+91 0000000000',
      gpsCoordinates: '20.5937,78.9629',
      ownerName: 'Distributor',
      reputationScore: 500,
    );
  }
}
