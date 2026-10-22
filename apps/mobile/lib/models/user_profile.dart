class UserProfile {
  final String id;
  final String email;
  final String? fullName;
  final String role; // admin, manufacturer, commuter, consumer
  final String? organization;
  final String? walletAddress;

  UserProfile({
    required this.id,
    required this.email,
    this.fullName,
    required this.role,
    this.organization,
    this.walletAddress,
  });

  factory UserProfile.fromJson(Map<String, dynamic> json) {
    return UserProfile(
      id: json['id'] ?? '',
      email: json['email'] ?? '',
      fullName: json['full_name'],
      role: json['role'] ?? 'consumer',
      organization: json['organization'],
      walletAddress: json['wallet_address'],
    );
  }
}
