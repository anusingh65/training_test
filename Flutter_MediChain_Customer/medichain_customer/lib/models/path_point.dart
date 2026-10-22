// lib/models/path_point.dart

class PathPoint {
  final String location;
  final DateTime timestamp;
  final String action;
  final String actor;
  final String? transactionHash;

  PathPoint({
    required this.location,
    required this.timestamp,
    required this.action,
    required this.actor,
    this.transactionHash,
  });

  // Convert from JSON (for real API responses)
  factory PathPoint.fromJson(Map<String, dynamic> json) {
    return PathPoint(
      location: json['location'] as String? ?? 'Unknown Location',
      timestamp: DateTime.tryParse(json['timestamp'] as String? ?? '') ?? DateTime.now(),
      action: json['action'] as String? ?? 'Unknown Action',
      actor: json['actor'] as String? ?? 'Unknown Actor',
      transactionHash: json['transaction_hash'] as String?,
    );
  }

  // Convert to JSON (for storage if needed)
  Map<String, dynamic> toJson() => {
    'location': location,
    'timestamp': timestamp.toIso8601String(),
    'action': action,
    'actor': actor,
    'transaction_hash': transactionHash,
  };

  // Helper to format time nicely
  String get formattedTime {
    return '${timestamp.year}-${timestamp.month.toString().padLeft(2, '0')}-${timestamp.day.toString().padLeft(2, '0')} '
        '${timestamp.hour.toString().padLeft(2, '0')}:${timestamp.minute.toString().padLeft(2, '0')}';
  }
}