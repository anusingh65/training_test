class BatchModel {
  final int batchId;
  final String batchNumber;
  final int totalUnits;
  final int registeredUnits;
  final String ipfsHash;
  final String contentHash;
  final String manufacturer;
  final DateTime createdAt;
  final bool isComplete;

  // Medicine details (not stored on blockchain, used for IPFS)
  final String medicineName;
  final String composition;
  final String dosage;
  final DateTime manufactureDate;
  final DateTime expiryDate;
  final String manufacturerName;
  final String manufacturerLicense;
  final String manufacturerLocation;
  final int pillsPerStrip;

  BatchModel({
    required this.batchId,
    required this.batchNumber,
    required this.totalUnits,
    this.registeredUnits = 0,
    this.ipfsHash = '',
    this.contentHash = '',
    required this.manufacturer,
    DateTime? createdAt,
    this.isComplete = false,
    required this.medicineName,
    required this.composition,
    required this.dosage,
    required this.manufactureDate,
    required this.expiryDate,
    required this.manufacturerName,
    required this.manufacturerLicense,
    required this.manufacturerLocation,
    this.pillsPerStrip = 0,
  }) : createdAt = createdAt ?? DateTime.now();

  // Convert to JSON for IPFS storage
  Map<String, dynamic> toJson() {
    return {
      'batch_id': batchId,
      'batch_number': batchNumber,
      'total_units': totalUnits,
      'pills_per_strip': pillsPerStrip,
      'medicine_name': medicineName,
      'composition': composition,
      'dosage': dosage,
      'manufacture_date': manufactureDate.toIso8601String(),
      'expiry_date': expiryDate.toIso8601String(),
      'manufacturer': {
        'name': manufacturerName,
        'license': manufacturerLicense,
        'location': manufacturerLocation,
        'address': manufacturer,
      },
      'created_at': createdAt.toIso8601String(),
      'schema_version': '1.0',
      'type': 'batch_metadata',
    };
  }

  // Create from JSON (from IPFS)
  factory BatchModel.fromJson(Map<String, dynamic> json) {
    return BatchModel(
      batchId: json['batch_id'] ?? 0,
      batchNumber: json['batch_number'] ?? '',
      totalUnits: json['total_units'] ?? 0,
      manufacturer: json['manufacturer']?['address'] ?? '',
      medicineName: json['medicine_name'] ?? '',
      composition: json['composition'] ?? '',
      dosage: json['dosage'] ?? '',
      manufactureDate: DateTime.parse(json['manufacture_date']),
      expiryDate: DateTime.parse(json['expiry_date']),
      manufacturerName: json['manufacturer']?['name'] ?? '',
      manufacturerLicense: json['manufacturer']?['license'] ?? '',
      manufacturerLocation: json['manufacturer']?['location'] ?? '',
      pillsPerStrip: json['pills_per_strip'] ?? 0,
      createdAt: json['created_at'] != null
          ? DateTime.parse(json['created_at'])
          : DateTime.now(),
    );
  }

  // Copy with method
  BatchModel copyWith({
    int? registeredUnits,
    String? ipfsHash,
    String? contentHash,
    bool? isComplete,
  }) {
    return BatchModel(
      batchId: batchId,
      batchNumber: batchNumber,
      totalUnits: totalUnits,
      registeredUnits: registeredUnits ?? this.registeredUnits,
      ipfsHash: ipfsHash ?? this.ipfsHash,
      contentHash: contentHash ?? this.contentHash,
      manufacturer: manufacturer,
      createdAt: createdAt,
      isComplete: isComplete ?? this.isComplete,
      medicineName: medicineName,
      composition: composition,
      dosage: dosage,
      manufactureDate: manufactureDate,
      expiryDate: expiryDate,
      manufacturerName: manufacturerName,
      manufacturerLicense: manufacturerLicense,
      manufacturerLocation: manufacturerLocation,
      pillsPerStrip: pillsPerStrip,
    );
  }

  // Calculate completion percentage
  double get completionPercentage {
    if (totalUnits == 0) return 0.0;
    return (registeredUnits / totalUnits) * 100;
  }

  // Check if expired
  bool get isExpired {
    return DateTime.now().isAfter(expiryDate);
  }

  // Get days until expiry
  int get daysUntilExpiry {
    return expiryDate.difference(DateTime.now()).inDays;
  }
}
