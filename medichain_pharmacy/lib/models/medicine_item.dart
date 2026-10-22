/// Represents a medicine unit owned by the pharmacy (on-chain state).
class MedicineItem {
  final int id;
  final int batchId;
  final String ipfsHash;
  final String contentHash;
  final String currentOwner;
  final int status; // State enum from contract
  final String? batchNumber;
  final String? manufacturer;

  MedicineItem({
    required this.id,
    required this.batchId,
    required this.ipfsHash,
    required this.contentHash,
    required this.currentOwner,
    required this.status,
    this.batchNumber,
    this.manufacturer,
  });

  String get statusLabel {
    switch (status) {
      case 0:
        return 'Manufactured';
      case 1:
        return 'In Transit';
      case 2:
        return 'At Distributor';
      case 3:
        return 'At Pharmacy';
      case 4:
        return 'Dispensed';
      case 5:
        return 'Flagged';
      default:
        return 'Unknown';
    }
  }

  bool get isAtPharmacy => status == 3;
  bool get isDispensed => status == 4;
  bool get isFlagged => status == 5;

  String get shortId => id.toString().padLeft(6, '0');

  Map<String, dynamic> toJson() => {
        'id': id,
        'batchId': batchId,
        'ipfsHash': ipfsHash,
        'contentHash': contentHash,
        'currentOwner': currentOwner,
        'status': status,
        'batchNumber': batchNumber,
        'manufacturer': manufacturer,
      };

  factory MedicineItem.fromJson(Map<String, dynamic> json) => MedicineItem(
        id: json['id'],
        batchId: json['batchId'],
        ipfsHash: json['ipfsHash'] ?? '',
        contentHash: json['contentHash'] ?? '',
        currentOwner: json['currentOwner'] ?? '',
        status: json['status'] ?? 0,
        batchNumber: json['batchNumber'],
        manufacturer: json['manufacturer'],
      );
}
