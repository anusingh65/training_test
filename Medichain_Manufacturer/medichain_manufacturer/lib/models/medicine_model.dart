class MedicineModel {
  final int medicineId;
  final int batchId;
  final String ipfsHash;
  final String contentHash;
  final String qrData;

  // Details from batch (for IPFS metadata)
  final String medicineName;
  final String composition;
  final String dosage;
  final String batchNumber;
  final DateTime manufactureDate;
  final DateTime expiryDate;
  final int pillsPerStrip;

  MedicineModel({
    required this.medicineId,
    required this.batchId,
    this.ipfsHash = '',
    this.contentHash = '',
    String? qrData,
    required this.medicineName,
    required this.composition,
    required this.dosage,
    required this.batchNumber,
    required this.manufactureDate,
    required this.expiryDate,
    this.pillsPerStrip = 0,
  }) : qrData = qrData ?? '{"type":"medicine","id":$medicineId,"batch_id":$batchId,"contract":"0x42b07481379ce4beF2aC70BC0329bD29a2E7cb8A","network":"sepolia"}';

  // Convert to JSON for IPFS storage
  Map<String, dynamic> toJson() {
    return {
      'medicine_id': medicineId,
      'batch_id': batchId,
      'batch_number': batchNumber,
      'name': medicineName,
      'composition': composition,
      'dosage': dosage,
      'pills_per_strip': pillsPerStrip,
      'manufacture_date': manufactureDate.toIso8601String(),
      'expiry_date': expiryDate.toIso8601String(),
      'uploaded_at': DateTime.now().toIso8601String(),
      'schema_version': '1.0',
      'type': 'medicine_metadata',
    };
  }

  // Create from JSON (from IPFS)
  factory MedicineModel.fromJson(Map<String, dynamic> json) {
    return MedicineModel(
      medicineId: json['medicine_id'] ?? 0,
      batchId: json['batch_id'] ?? 0,
      batchNumber: json['batch_number'] ?? '',
      medicineName: json['name'] ?? '',
      composition: json['composition'] ?? '',
      dosage: json['dosage'] ?? '',
      manufactureDate: DateTime.parse(json['manufacture_date']),
      expiryDate: DateTime.parse(json['expiry_date']),
      ipfsHash: json['ipfs_hash'] ?? '',
      pillsPerStrip: json['pills_per_strip'] ?? 0,
    );
  }

  // Copy with method
  MedicineModel copyWith({
    String? ipfsHash,
    String? contentHash,
    String? qrData,
  }) {
    return MedicineModel(
      medicineId: medicineId,
      batchId: batchId,
      ipfsHash: ipfsHash ?? this.ipfsHash,
      contentHash: contentHash ?? this.contentHash,
      qrData: qrData ?? this.qrData,
      medicineName: medicineName,
      composition: composition,
      dosage: dosage,
      batchNumber: batchNumber,
      manufactureDate: manufactureDate,
      expiryDate: expiryDate,
      pillsPerStrip: pillsPerStrip,
    );
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
