class DrugModel {
  final String manufacturerPublicKey;
  final String name;
  final String composition;
  final String dosage;
  final int pillsPerStrip;
  final int expiryFromManufacture; // months from manufacture date

  DrugModel({
    required this.manufacturerPublicKey,
    required this.name,
    required this.composition,
    required this.dosage,
    required this.pillsPerStrip,
    required this.expiryFromManufacture,
  });

  factory DrugModel.fromJson(Map<String, dynamic> json) {
    return DrugModel(
      manufacturerPublicKey: json['manufacturer_public_key'] ?? '',
      name: json['name'] ?? '',
      composition: json['composition'] ?? '',
      dosage: json['dosage'] ?? '',
      pillsPerStrip: json['pills_per_strip'] ?? 0,
      expiryFromManufacture: json['expiry_from_manufacture'] ?? 0,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'manufacturer_public_key': manufacturerPublicKey,
      'name': name,
      'composition': composition,
      'dosage': dosage,
      'pills_per_strip': pillsPerStrip,
      'expiry_from_manufacture': expiryFromManufacture,
    };
  }

  /// Calculate expiry date from a given manufacture date
  DateTime calculateExpiryDate(DateTime manufactureDate) {
    return DateTime(
      manufactureDate.year,
      manufactureDate.month + expiryFromManufacture,
      manufactureDate.day,
    );
  }
}
