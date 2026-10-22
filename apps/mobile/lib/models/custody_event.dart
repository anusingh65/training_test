class CustodyEvent {
  final String id;
  final String drugId;
  final String? fromEntity;
  final String? toEntity;
  final String eventType;
  final String? location;
  final double? latitude;
  final double? longitude;
  final String? blockchainTxHash;
  final DateTime timestamp;

  CustodyEvent({
    required this.id,
    required this.drugId,
    this.fromEntity,
    this.toEntity,
    required this.eventType,
    this.location,
    this.latitude,
    this.longitude,
    this.blockchainTxHash,
    required this.timestamp,
  });

  factory CustodyEvent.fromJson(Map<String, dynamic> json) {
    return CustodyEvent(
      id: json['id'] ?? '',
      drugId: json['drug_id'] ?? '',
      fromEntity: json['from_entity'],
      toEntity: json['to_entity'],
      eventType: json['event_type'] ?? '',
      location: json['location'],
      latitude: (json['latitude'] as num?)?.toDouble(),
      longitude: (json['longitude'] as num?)?.toDouble(),
      blockchainTxHash: json['blockchain_tx_hash'],
      timestamp: DateTime.parse(json['timestamp'] ?? DateTime.now().toIso8601String()),
    );
  }
}
