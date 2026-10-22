import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:go_router/go_router.dart';
import '../../config/theme.dart';
import '../../models/scan_result.dart';
import '../../widgets/verification_badge.dart';

class ResultScreen extends StatelessWidget {
  final Map<String, dynamic> data;

  const ResultScreen({super.key, required this.data});

  @override
  Widget build(BuildContext context) {
    final result = data['scanResult'] as ScanResult?;
    final qrData = data['qrData'] as Map<String, String>?;

    if (result == null) {
      return Scaffold(
        appBar: AppBar(title: const Text('Result')),
        body: const Center(child: Text('No scan data')),
      );
    }

    final Color statusColor;
    final IconData statusIcon;
    switch (result.status) {
      case 'verified':
        statusColor = AppColors.verified;
        statusIcon = Icons.check_circle;
        break;
      case 'suspicious':
        statusColor = AppColors.suspicious;
        statusIcon = Icons.warning;
        break;
      default:
        statusColor = AppColors.counterfeit;
        statusIcon = Icons.dangerous;
    }

    return Scaffold(
      appBar: AppBar(title: const Text('Verification Result')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Column(
          children: [
            // Status card
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(32),
              decoration: BoxDecoration(
                color: statusColor.withOpacity(0.1),
                borderRadius: BorderRadius.circular(20),
                border: Border.all(color: statusColor.withOpacity(0.3)),
              ),
              child: Column(
                children: [
                  Icon(statusIcon, size: 72, color: statusColor),
                  const SizedBox(height: 16),
                  Text(
                    result.status.toUpperCase(),
                    style: TextStyle(
                      fontSize: 28,
                      fontWeight: FontWeight.bold,
                      color: statusColor,
                    ),
                  ),
                  const SizedBox(height: 8),
                  VerificationBadge(status: result.status),
                ],
              ),
            ),
            const SizedBox(height: 24),

            // Risk score
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    const Text('Risk Score', style: TextStyle(color: Colors.grey)),
                    Text(
                      '${result.riskScore.toStringAsFixed(1)}%',
                      style: TextStyle(
                        fontSize: 24,
                        fontWeight: FontWeight.bold,
                        color: statusColor,
                      ),
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 12),

            // Drug info
            if (result.drugInfo != null) ...[
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text('Drug Information', style: TextStyle(fontWeight: FontWeight.w600, fontSize: 16)),
                      const SizedBox(height: 12),
                      _infoRow('Drug ID', result.drugId),
                      _infoRow('Name', result.drugInfo!['name'] ?? ''),
                      _infoRow('Manufacturer', result.drugInfo!['manufacturer'] ?? ''),
                      _infoRow('Batch', result.drugInfo!['batchId'] ?? ''),
                      _infoRow('Hash Match', result.hashMatch ? 'Yes' : 'No'),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 12),
            ],

            // Risk factors
            if (result.riskFactors.isNotEmpty) ...[
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text('Risk Factors', style: TextStyle(fontWeight: FontWeight.w600, fontSize: 16)),
                      const SizedBox(height: 12),
                      ...result.riskFactors.map((f) => Padding(
                            padding: const EdgeInsets.only(bottom: 8),
                            child: Row(
                              children: [
                                const Icon(Icons.warning_amber, size: 16, color: AppColors.suspicious),
                                const SizedBox(width: 8),
                                Expanded(child: Text(f, style: const TextStyle(fontSize: 13))),
                              ],
                            ),
                          )),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 12),
            ],

            // Actions
            Row(
              children: [
                Expanded(
                  child: ElevatedButton.icon(
                    onPressed: () => context.push('/drug/${result.drugId}'),
                    icon: const Icon(Icons.info_outline),
                    label: const Text('Details'),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: ElevatedButton.icon(
                    onPressed: () => context.push('/report/${result.drugId}'),
                    icon: const Icon(Icons.flag_outlined),
                    label: const Text('Report'),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: AppColors.counterfeit,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            SizedBox(
              width: double.infinity,
              child: OutlinedButton(
                onPressed: () => context.go('/home'),
                child: const Text('Scan Another'),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _infoRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: const TextStyle(color: Colors.grey, fontSize: 13)),
          Text(value, style: const TextStyle(fontSize: 13)),
        ],
      ),
    );
  }
}
