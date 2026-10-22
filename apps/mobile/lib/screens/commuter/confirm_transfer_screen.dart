import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:url_launcher/url_launcher.dart';
import '../../config/theme.dart';
import '../../models/drug.dart';
import '../../providers/drug_provider.dart';
import '../../services/location_service.dart';

class ConfirmTransferScreen extends ConsumerStatefulWidget {
  final Map<String, dynamic> data;

  const ConfirmTransferScreen({super.key, required this.data});

  @override
  ConsumerState<ConfirmTransferScreen> createState() => _ConfirmTransferScreenState();
}

class _ConfirmTransferScreenState extends ConsumerState<ConfirmTransferScreen> {
  bool _loading = false;
  String? _txHash;
  String? _error;

  Future<void> _confirmReceipt() async {
    setState(() {
      _loading = true;
      _error = null;
    });

    try {
      final drug = widget.data['drug'] as Drug;
      final blockchain = ref.read(blockchainServiceProvider);
      final locationService = LocationService();
      final pos = await locationService.getCurrentPosition();
      final location = pos != null ? '${pos.latitude},${pos.longitude}' : 'Unknown';

      // Get wallet address for 'to'
      final wallet = await blockchain.getOrCreateWallet();

      final txHash = await blockchain.transferCustody(
        drugId: drug.drugId,
        toAddress: wallet.hex,
        eventType: 'received',
        location: location,
      );

      if (txHash != null) {
        // Also record in Supabase
        final drugService = ref.read(drugServiceProvider);
        await drugService.getDrug(drug.drugId); // refresh

        setState(() => _txHash = txHash);
      } else {
        setState(() => _error = 'Transaction failed. Check wallet balance.');
      }
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final drug = widget.data['drug'] as Drug?;

    if (drug == null) {
      return Scaffold(
        appBar: AppBar(title: const Text('Confirm Transfer')),
        body: const Center(child: Text('No drug data')),
      );
    }

    return Scaffold(
      appBar: AppBar(title: const Text('Confirm Receipt')),
      body: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(drug.name,
                        style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                    const SizedBox(height: 12),
                    _row('Drug ID', drug.drugId),
                    _row('Batch', drug.batchId),
                    _row('Manufacturer', drug.manufacturer),
                    _row('Status', drug.status),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 24),

            if (_txHash != null) ...[
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(20),
                decoration: BoxDecoration(
                  color: AppColors.verified.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: AppColors.verified.withOpacity(0.3)),
                ),
                child: Column(
                  children: [
                    const Icon(Icons.check_circle, size: 48, color: AppColors.verified),
                    const SizedBox(height: 12),
                    const Text('Transfer Confirmed',
                        style: TextStyle(
                            fontWeight: FontWeight.bold, fontSize: 18, color: AppColors.verified)),
                    const SizedBox(height: 12),
                    GestureDetector(
                      onTap: () => launchUrl(
                          Uri.parse('https://amoy.polygonscan.com/tx/$_txHash')),
                      child: Text(
                        'View on Polygonscan',
                        style: TextStyle(
                            color: AppColors.primary, decoration: TextDecoration.underline),
                      ),
                    ),
                  ],
                ),
              ),
              const Spacer(),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  onPressed: () => context.go('/commuter'),
                  child: const Text('Back to Home'),
                ),
              ),
            ] else ...[
              if (_error != null)
                Padding(
                  padding: const EdgeInsets.only(bottom: 16),
                  child: Text(_error!,
                      style: const TextStyle(color: AppColors.counterfeit, fontSize: 13)),
                ),
              const Spacer(),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  onPressed: _loading ? null : _confirmReceipt,
                  child: _loading
                      ? const SizedBox(
                          height: 20,
                          width: 20,
                          child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                        )
                      : const Text('Confirm Receipt on Blockchain'),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _row(String label, String value) {
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
