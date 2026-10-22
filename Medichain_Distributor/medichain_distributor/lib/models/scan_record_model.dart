class ScanRecordModel {
  final String scanner;
  final double latitude;
  final double longitude;
  final DateTime timestamp;
  final String location;
  final String deviceId;

  ScanRecordModel({
    required this.scanner,
    required this.latitude,
    required this.longitude,
    required this.timestamp,
    required this.location,
    required this.deviceId,
  });

  factory ScanRecordModel.fromBlockchain(List<dynamic> tuple) {
    return ScanRecordModel(
      scanner: tuple[0].toString(),
      latitude: (tuple[1] as BigInt).toDouble() / 1e6,
      longitude: (tuple[2] as BigInt).toDouble() / 1e6,
      timestamp: DateTime.fromMillisecondsSinceEpoch(
        (tuple[3] as BigInt).toInt() * 1000,
      ),
      location: tuple[4] as String,
      deviceId: tuple[5] as String,
    );
  }

  factory ScanRecordModel.fromJson(Map<String, dynamic> json) {
    return ScanRecordModel(
      scanner: json['scanner'] ?? '',
      latitude: (json['latitude'] ?? 0).toDouble(),
      longitude: (json['longitude'] ?? 0).toDouble(),
      timestamp: json['timestamp'] != null
          ? DateTime.fromMillisecondsSinceEpoch(json['timestamp'] * 1000)
          : DateTime.now(),
      location: json['location'] ?? '',
      deviceId: json['deviceId'] ?? '',
    );
  }

  Map<String, dynamic> toJson() => {
    'scanner': scanner,
    'latitude': latitude,
    'longitude': longitude,
    'timestamp': timestamp.millisecondsSinceEpoch ~/ 1000,
    'location': location,
    'deviceId': deviceId,
  };
}
