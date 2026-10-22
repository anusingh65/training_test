import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../config/theme.dart';
import '../../providers/drug_provider.dart';
import '../../services/location_service.dart';

class ReportScreen extends ConsumerStatefulWidget {
  final String drugId;

  const ReportScreen({super.key, required this.drugId});

  @override
  ConsumerState<ReportScreen> createState() => _ReportScreenState();
}

class _ReportScreenState extends ConsumerState<ReportScreen> {
  String _reason = 'Hash mismatch';
  final _descController = TextEditingController();
  bool _loading = false;

  final _reasons = [
    'Hash mismatch',
    'Suspicious packaging',
    'Expired product',
    'Geographic anomaly',
    'Duplicate batch',
    'Other',
  ];

  Future<void> _submit() async {
    setState(() => _loading = true);

    try {
      final locationService = LocationService();
      final pos = await locationService.getCurrentPosition();

      final drugService = ref.read(drugServiceProvider);
      await drugService.flagDrug(
        drugId: widget.drugId,
        reason: _reason,
        description: _descController.text.trim(),
        latitude: pos?.latitude,
        longitude: pos?.longitude,
      );

      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Report submitted successfully'),
          backgroundColor: AppColors.verified,
        ),
      );
      context.pop();
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error: $e'), backgroundColor: AppColors.counterfeit),
        );
      }
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Report Drug')),
      body: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Drug: ${widget.drugId}',
                style: const TextStyle(fontWeight: FontWeight.w600)),
            const SizedBox(height: 20),

            const Text('Reason', style: TextStyle(color: Colors.grey, fontSize: 13)),
            const SizedBox(height: 8),
            DropdownButtonFormField<String>(
              value: _reason,
              decoration: const InputDecoration(border: OutlineInputBorder()),
              items: _reasons
                  .map((r) => DropdownMenuItem(value: r, child: Text(r)))
                  .toList(),
              onChanged: (v) => setState(() => _reason = v!),
            ),
            const SizedBox(height: 20),

            const Text('Description (optional)',
                style: TextStyle(color: Colors.grey, fontSize: 13)),
            const SizedBox(height: 8),
            TextField(
              controller: _descController,
              maxLines: 4,
              decoration: const InputDecoration(
                border: OutlineInputBorder(),
                hintText: 'Describe the issue...',
              ),
            ),
            const Spacer(),

            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: _loading ? null : _submit,
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppColors.counterfeit,
                ),
                child: _loading
                    ? const SizedBox(
                        height: 20,
                        width: 20,
                        child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                      )
                    : const Text('Submit Report'),
              ),
            ),
          ],
        ),
      ),
    );
  }

  @override
  void dispose() {
    _descController.dispose();
    super.dispose();
  }
}
