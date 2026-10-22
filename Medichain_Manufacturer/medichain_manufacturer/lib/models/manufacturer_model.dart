class ManufacturerModel {
  final String address;
  final String name;
  final String license;
  final String location;
  final int role;
  final bool isActive;
  final String? mobileNo;
  final String? gpsCoordinates;
  final String? ownerName;

  ManufacturerModel({
    required this.address,
    required this.name,
    required this.license,
    required this.location,
    this.role = 1, // Role.Manufacturer
    this.isActive = true,
    this.mobileNo,
    this.gpsCoordinates,
    this.ownerName,
  });

  // Convert to JSON
  Map<String, dynamic> toJson() {
    return {
      'address': address,
      'name': name,
      'license': license,
      'location': location,
      'role': role,
      'is_active': isActive,
      if (mobileNo != null) 'mobile_no': mobileNo,
      if (gpsCoordinates != null) 'gps_coordinates': gpsCoordinates,
      if (ownerName != null) 'owner_name': ownerName,
    };
  }

  // Create from JSON
  factory ManufacturerModel.fromJson(Map<String, dynamic> json) {
    return ManufacturerModel(
      address: json['address'] ?? json['public_key'] ?? '',
      name: json['name'] ?? '',
      license: json['license'] ?? json['license_number'] ?? '',
      location: json['location'] ?? json['address'] ?? '',
      role: json['role'] ?? 1,
      isActive: json['is_active'] ?? true,
      mobileNo: json['mobile_no'],
      gpsCoordinates: json['gps_coordinates'],
      ownerName: json['owner_name'],
    );
  }

  // Copy with method
  ManufacturerModel copyWith({
    String? address,
    String? name,
    String? license,
    String? location,
    int? role,
    bool? isActive,
    String? mobileNo,
    String? gpsCoordinates,
    String? ownerName,
  }) {
    return ManufacturerModel(
      address: address ?? this.address,
      name: name ?? this.name,
      license: license ?? this.license,
      location: location ?? this.location,
      role: role ?? this.role,
      isActive: isActive ?? this.isActive,
      mobileNo: mobileNo ?? this.mobileNo,
      gpsCoordinates: gpsCoordinates ?? this.gpsCoordinates,
      ownerName: ownerName ?? this.ownerName,
    );
  }

  // Get shortened address for display (0x1234...5678)
  String get shortAddress {
    if (address.length < 10) return address;
    return '${address.substring(0, 6)}...${address.substring(address.length - 4)}';
  }
}
