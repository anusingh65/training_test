class ScanResult {
  final String drugId;
  final String status; // verified, suspicious, counterfeit
  final bool hashMatch;
  final double riskScore;
  final String riskLevel;
  final List<String> riskFactors;
  final Map<String, dynamic>? drugInfo;

  ScanResult({
    required this.drugId,
    required this.status,
    required this.hashMatch,
    required this.riskScore,
    required this.riskLevel,
    this.riskFactors = const [],
    this.drugInfo,
  });
}
