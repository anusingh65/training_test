class MedicineModel {
  final int id;
  final int batchId;
  final String ipfsHash;
  final String contentHash;
  final String currentOwner;
  final String manufacturer;
  final int status;
  final int transferCount;
  final int scanCount;
  final int flagCount;
  final bool isFlagged;

  MedicineModel({
    required this.id,
    required this.batchId,
    required this.ipfsHash,
    required this.contentHash,
    required this.currentOwner,
    required this.manufacturer,
    required this.status,
    required this.transferCount,
    required this.scanCount,
    required this.flagCount,
    required this.isFlagged,
  });

  factory MedicineModel.fromJson(Map<String, dynamic> json) {
    return MedicineModel(
      id: json['id'] ?? 0,
      batchId: json['batchId'] ?? 0,
      ipfsHash: json['ipfsHash'] ?? '',
      contentHash: json['contentHash'] ?? '',
      currentOwner: json['currentOwner'] ?? '',
      manufacturer: json['manufacturer'] ?? '',
      status: json['status'] ?? 0,
      transferCount: json['transferCount'] ?? 0,
      scanCount: json['scanCount'] ?? 0,
      flagCount: json['flagCount'] ?? 0,
      isFlagged: json['isFlagged'] ?? false,
    );
  }

  Map<String, dynamic> toJson() => {
    'id': id,
    'batchId': batchId,
    'ipfsHash': ipfsHash,
    'contentHash': contentHash,
    'currentOwner': currentOwner,
    'manufacturer': manufacturer,
    'status': status,
    'transferCount': transferCount,
    'scanCount': scanCount,
    'flagCount': flagCount,
    'isFlagged': isFlagged,
  };

  bool get isOwnedBy => false; // set dynamically
}
