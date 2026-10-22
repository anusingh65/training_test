class BatchModel {
  final int batchId;
  final String batchNumber;
  final String ipfsHash;
  final String manufacturer;
  final int totalUnits;
  final int registeredUnits;
  final DateTime createdAt;
  final bool isComplete;
  final List<int> medicineIds;

  BatchModel({
    required this.batchId,
    required this.batchNumber,
    required this.ipfsHash,
    required this.manufacturer,
    required this.totalUnits,
    required this.registeredUnits,
    required this.createdAt,
    required this.isComplete,
    this.medicineIds = const [],
  });

  factory BatchModel.fromJson(Map<String, dynamic> json) {
    return BatchModel(
      batchId: json['batchId'] ?? 0,
      batchNumber: json['batchNumber'] ?? '',
      ipfsHash: json['ipfsHash'] ?? '',
      manufacturer: json['manufacturer'] ?? '',
      totalUnits: json['totalUnits'] ?? 0,
      registeredUnits: json['registeredUnits'] ?? 0,
      createdAt: json['createdAt'] != null
          ? DateTime.fromMillisecondsSinceEpoch(json['createdAt'] * 1000)
          : DateTime.now(),
      isComplete: json['isComplete'] ?? false,
      medicineIds: (json['medicineIds'] as List?)?.cast<int>() ?? [],
    );
  }

  Map<String, dynamic> toJson() => {
    'batchId': batchId,
    'batchNumber': batchNumber,
    'ipfsHash': ipfsHash,
    'manufacturer': manufacturer,
    'totalUnits': totalUnits,
    'registeredUnits': registeredUnits,
    'createdAt': createdAt.millisecondsSinceEpoch ~/ 1000,
    'isComplete': isComplete,
    'medicineIds': medicineIds,
  };
}
