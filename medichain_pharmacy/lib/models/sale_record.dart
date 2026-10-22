import 'dart:convert';

/// A local record of a sale (ownership transfer to customer).
class SaleRecord {
  final int medicineId;
  final int batchId;
  final String customerAddress;
  final String txHash;
  final DateTime timestamp;
  final String? batchNumber;
  final String? customerName;

  SaleRecord({
    required this.medicineId,
    required this.batchId,
    required this.customerAddress,
    required this.txHash,
    required this.timestamp,
    this.batchNumber,
    this.customerName,
  });

  String get shortCustomer {
    if (customerAddress.length > 12) {
      return '${customerAddress.substring(0, 6)}...${customerAddress.substring(customerAddress.length - 4)}';
    }
    return customerAddress;
  }

  String get shortTx {
    if (txHash.length > 14) {
      return '${txHash.substring(0, 10)}...${txHash.substring(txHash.length - 4)}';
    }
    return txHash;
  }

  Map<String, dynamic> toJson() => {
        'medicineId': medicineId,
        'batchId': batchId,
        'customerAddress': customerAddress,
        'txHash': txHash,
        'timestamp': timestamp.toIso8601String(),
        'batchNumber': batchNumber,
        'customerName': customerName,
      };

  factory SaleRecord.fromJson(Map<String, dynamic> json) => SaleRecord(
        medicineId: json['medicineId'],
        batchId: json['batchId'],
        customerAddress: json['customerAddress'],
        txHash: json['txHash'],
        timestamp: DateTime.parse(json['timestamp']),
        batchNumber: json['batchNumber'],
        customerName: json['customerName'],
      );

  static String encodeList(List<SaleRecord> records) =>
      jsonEncode(records.map((r) => r.toJson()).toList());

  static List<SaleRecord> decodeList(String jsonStr) {
    final list = jsonDecode(jsonStr) as List;
    return list.map((e) => SaleRecord.fromJson(e)).toList();
  }
}
