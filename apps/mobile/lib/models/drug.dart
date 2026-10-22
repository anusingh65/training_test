class Drug {
  final String drugId;
  final String batchId;
  final String name;
  final String manufacturer;
  final String manufactureDate;
  final String expiryDate;
  final String metadataHash;
  final String qrHash;
  final String? ipfsCid;
  final String status;
  final bool flagged;

  Drug({
    required this.drugId,
    required this.batchId,
    required this.name,
    required this.manufacturer,
    required this.manufactureDate,
    required this.expiryDate,
    required this.metadataHash,
    required this.qrHash,
    this.ipfsCid,
    required this.status,
    required this.flagged,
  });

  factory Drug.fromJson(Map<String, dynamic> json) {
    return Drug(
      drugId: json['drug_id'] ?? '',
      batchId: json['batch_id'] ?? '',
      name: json['name'] ?? '',
      manufacturer: json['manufacturer'] ?? '',
      manufactureDate: json['manufacture_date'] ?? '',
      expiryDate: json['expiry_date'] ?? '',
      metadataHash: json['metadata_hash'] ?? '',
      qrHash: json['qr_hash'] ?? '',
      ipfsCid: json['ipfs_cid'],
      status: json['status'] ?? 'pending',
      flagged: json['flagged'] ?? false,
    );
  }
}
