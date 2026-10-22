class CustodyRecordModel {
  final String address;
  final DateTime timestamp;
  final String name;
  final String location;
  final int role;

  CustodyRecordModel({
    required this.address,
    required this.timestamp,
    this.name = '',
    this.location = '',
    this.role = 0,
  });

  CustodyRecordModel copyWith({
    String? name,
    String? location,
    int? role,
  }) {
    return CustodyRecordModel(
      address: address,
      timestamp: timestamp,
      name: name ?? this.name,
      location: location ?? this.location,
      role: role ?? this.role,
    );
  }
}
