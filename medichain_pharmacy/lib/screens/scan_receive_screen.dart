import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:mobile_scanner/mobile_scanner.dart';
import 'package:provider/provider.dart';
import '../models/medicine_item.dart';
import '../services/blockchain_service.dart';
import '../services/wallet_service.dart';
import '../services/inventory_service.dart';
import '../theme/app_theme.dart';

/// Scan a medicine QR code to add it to pharmacy inventory.
/// QR format: {"type":"medicine","id":int,"batch_id":int,...}
class ScanReceiveScreen extends StatefulWidget {
  const ScanReceiveScreen({super.key});

  @override
  State<ScanReceiveScreen> createState() => _ScanReceiveScreenState();
}

class _ScanReceiveScreenState extends State<ScanReceiveScreen> {
  final MobileScannerController _scannerCtrl = MobileScannerController();
  bool _processing = false;
  String? _result;
  bool _success = false;

  @override
  void dispose() {
    _scannerCtrl.dispose();
    super.dispose();
  }

  Future<void> _onDetect(BarcodeCapture capture) async {
    if (_processing) return;
    final barcode = capture.barcodes.firstOrNull;
    if (barcode?.rawValue == null) return;

    setState(() => _processing = true);
    await _scannerCtrl.stop();

    try {
      final data = jsonDecode(barcode!.rawValue!);
      final medicineId = data['id'] as int?;
      final batchId = data['batch_id'] as int?;

      if (medicineId == null || batchId == null) {
        throw Exception('Invalid QR: missing id or batch_id');
      }

      final blockchain = context.read<BlockchainService>();
      final wallet = context.read<WalletService>();
      final inventory = context.read<InventoryService>();

      // Fetch on-chain data
      final medicine = await blockchain.getMedicine(medicineId);
      if (medicine == null) {
        throw Exception('Medicine #$medicineId not found on chain');
      }

      // Verify the pharmacy currently owns it
      final myAddr = wallet.address!.toLowerCase();
      final owner = medicine.currentOwner.toLowerCase();

      if (owner != myAddr) {
        throw Exception(
            'You are not the current owner of this medicine.\nOwner: ${medicine.currentOwner}');
      }

      // Fetch batch info for display
      final batch = await blockchain.getBatch(batchId);
      final enriched = MedicineItem(
        id: medicine.id,
        batchId: medicine.batchId,
        ipfsHash: medicine.ipfsHash,
        contentHash: medicine.contentHash,
        currentOwner: medicine.currentOwner,
        status: medicine.status,
        batchNumber: batch?.batchNumber,
        manufacturer: batch?.manufacturer,
      );

      inventory.addMedicine(enriched);

      setState(() {
        _success = true;
        _result =
            'Medicine #$medicineId added to inventory\nBatch: ${batch?.batchNumber ?? batchId}';
      });
    } catch (e) {
      setState(() {
        _success = false;
        _result = e.toString();
      });
    }
  }

  void _scanAgain() {
    setState(() {
      _processing = false;
      _result = null;
      _success = false;
    });
    _scannerCtrl.start();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Receive Medicine'),
        centerTitle: true,
      ),
      body: _result != null ? _buildResult() : _buildScanner(),
    );
  }

  Widget _buildScanner() {
    return Stack(
      children: [
        MobileScanner(
          controller: _scannerCtrl,
          onDetect: _onDetect,
        ),
        // Overlay frame
        Center(
          child: Container(
            width: 280,
            height: 280,
            decoration: BoxDecoration(
              border: Border.all(color: AppColors.primary, width: 3),
              borderRadius: BorderRadius.circular(20),
            ),
          ),
        ),
        // Bottom instructions
        Positioned(
          bottom: 60,
          left: 0,
          right: 0,
          child: Center(
            child: Container(
              padding: const EdgeInsets.symmetric(
                  horizontal: AppSpacing.lg, vertical: AppSpacing.md),
              decoration: BoxDecoration(
                color: Colors.black.withValues(alpha: 0.7),
                borderRadius: BorderRadius.circular(12),
              ),
              child: Text(
                'Scan medicine QR code to receive',
                style: AppTypography.bodyMedium.copyWith(color: Colors.white),
              ),
            ),
          ),
        ),
        if (_processing)
          Container(
            color: Colors.black54,
            child: const Center(
              child: CircularProgressIndicator(color: Colors.white),
            ),
          ),
      ],
    );
  }

  Widget _buildResult() {
    return Center(
      child: SingleChildScrollView(
        padding: const EdgeInsets.all(AppSpacing.lg),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(
              width: 100,
              height: 100,
              decoration: BoxDecoration(
                color: (_success ? AppColors.success : AppColors.error)
                    .withValues(alpha: 0.1),
                shape: BoxShape.circle,
              ),
              child: Icon(
                _success ? Icons.check_circle : Icons.error_outline,
                size: 56,
                color: _success ? AppColors.success : AppColors.error,
              ),
            )
                .animate()
                .scaleXY(
                    begin: 0.5, end: 1, duration: 500.ms,
                    curve: Curves.easeOutBack),

            const SizedBox(height: AppSpacing.lg),

            Text(
              _success ? 'Medicine Received' : 'Error',
              style: AppTypography.displayMedium,
            ).animate().fadeIn(duration: 400.ms, delay: 200.ms),

            const SizedBox(height: AppSpacing.md),

            Container(
              padding: const EdgeInsets.all(AppSpacing.md),
              decoration: BoxDecoration(
                color: (_success ? AppColors.success : AppColors.error)
                    .withValues(alpha: 0.05),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(
                  color: (_success ? AppColors.success : AppColors.error)
                      .withValues(alpha: 0.2),
                ),
              ),
              child: Text(
                _result ?? '',
                style: AppTypography.bodyLarge,
                textAlign: TextAlign.center,
              ),
            ).animate().fadeIn(duration: 400.ms, delay: 400.ms),

            const SizedBox(height: AppSpacing.xl),

            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                OutlinedButton.icon(
                  onPressed: () => Navigator.pop(context),
                  icon: const Icon(Icons.arrow_back),
                  label: const Text('Back'),
                ),
                const SizedBox(width: AppSpacing.md),
                ElevatedButton.icon(
                  onPressed: _scanAgain,
                  icon: const Icon(Icons.qr_code_scanner),
                  label: const Text('Scan Another'),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: AppColors.primary,
                    foregroundColor: Colors.white,
                  ),
                ),
              ],
            ).animate().fadeIn(duration: 400.ms, delay: 600.ms),
          ],
        ),
      ),
    );
  }
}
