class DistributorModel {
  final String address;
  final String name;
  final String license;
  final String location;
  final String mobileNo;
  final String gpsCoordinates;
  final String ownerName;
  final int reputationScore;

  DistributorModel({
    required this.address,
    required this.name,
    required this.license,
    required this.location,
    required this.mobileNo,
    required this.gpsCoordinates,
    required this.ownerName,
    required this.reputationScore,
  });

  factory DistributorModel.fromJson(Map<String, dynamic> json) {
    return DistributorModel(
      address: json['public_key'] ?? '',
      name: json['name'] ?? '',
      license: json['license_number'] ?? '',
      location: json['address'] ?? '',
      mobileNo: json['mobile_no'] ?? '',
      gpsCoordinates: json['gps_coordinates'] ?? '',
      ownerName: json['owner_name'] ?? '',
      reputationScore: json['reputation_score'] ?? 500,
    );
  }

  Map<String, dynamic> toJson() => {
    'public_key': address,
    'name': name,
    'license_number': license,
    'address': location,
    'mobile_no': mobileNo,
    'gps_coordinates': gpsCoordinates,
    'owner_name': ownerName,
    'reputation_score': reputationScore,
  };
}
