import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:mobile_scanner/mobile_scanner.dart';
import 'package:provider/provider.dart';
import '../models/medicine_item.dart';
import '../models/sale_record.dart';
import '../services/blockchain_service.dart';
import '../services/wallet_service.dart';
import '../services/inventory_service.dart';
import '../theme/app_theme.dart';

class SellMedicineScreen extends StatefulWidget {
  const SellMedicineScreen({super.key});

  @override
  State<SellMedicineScreen> createState() => _SellMedicineScreenState();
}

class _SellMedicineScreenState extends State<SellMedicineScreen> {
  final _customerController = TextEditingController();
  final _customerNameController = TextEditingController();
  MedicineItem? _selectedMedicine;
  bool _isTransferring = false;
  String? _error;
  String? _txHash;

  // Step: 0=select medicine, 1=enter customer, 2=confirm, 3=done
  int _step = 0;

  @override
  void dispose() {
    _customerController.dispose();
    _customerNameController.dispose();
    super.dispose();
  }

  // ── Step 0: Select Medicine ───────────────────────────────────────────────

  Widget _buildSelectMedicine() {
    final inv = context.watch<InventoryService>();
    final available = inv.availableInventory;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text('Select Medicine to Sell', style: AppTypography.titleLarge),
        const SizedBox(height: AppSpacing.xs),
        Text(
          '${available.length} items available in inventory',
          style: AppTypography.bodyMedium,
        ),
        const SizedBox(height: AppSpacing.lg),

        // Scan option
        SizedBox(
          width: double.infinity,
          child: OutlinedButton.icon(
            onPressed: _scanMedicineQR,
            icon: const Icon(Icons.qr_code_scanner),
            label: const Text('Scan Medicine QR'),
            style: OutlinedButton.styleFrom(
              padding: const EdgeInsets.symmetric(vertical: 14),
            ),
          ),
        ),

        const SizedBox(height: AppSpacing.lg),

        if (available.isEmpty)
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(AppSpacing.xl),
            decoration: AppDecorations.card,
            child: Column(
              children: [
                Icon(Icons.inventory_2_outlined,
                    size: 48, color: AppColors.textTertiary),
                const SizedBox(height: AppSpacing.sm),
                Text('No medicines in stock', style: AppTypography.bodyMedium),
                Text(
                  'Receive medicines first using the Scan & Receive feature',
                  style: AppTypography.bodySmall,
                  textAlign: TextAlign.center,
                ),
              ],
            ),
          )
        else
          Text('Or select from inventory:', style: AppTypography.titleSmall),

        const SizedBox(height: AppSpacing.sm),

        ...available.map(
          (med) => Container(
            margin: const EdgeInsets.only(bottom: AppSpacing.sm),
            child: Material(
              color: Colors.transparent,
              child: InkWell(
                borderRadius: BorderRadius.circular(16),
                onTap: () {
                  HapticFeedback.selectionClick();
                  setState(() {
                    _selectedMedicine = med;
                    _step = 1;
                  });
                },
                child: Container(
                  padding: const EdgeInsets.all(AppSpacing.md),
                  decoration: AppDecorations.card,
                  child: Row(
                    children: [
                      Container(
                        width: 44,
                        height: 44,
                        decoration: BoxDecoration(
                          color: AppColors.primary.withValues(alpha: 0.1),
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: Center(
                          child: Text(
                            '#${med.shortId}',
                            style: AppTypography.bodySmall.copyWith(
                              color: AppColors.primary,
                              fontWeight: FontWeight.w600,
                              fontSize: 10,
                            ),
                          ),
                        ),
                      ),
                      const SizedBox(width: AppSpacing.md),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text('Medicine #${med.id}',
                                style: AppTypography.titleSmall),
                            Text(
                              'Batch: ${med.batchNumber ?? med.batchId}',
                              style: AppTypography.bodySmall,
                            ),
                          ],
                        ),
                      ),
                      Container(
                        padding: const EdgeInsets.symmetric(
                            horizontal: 10, vertical: 4),
                        decoration: BoxDecoration(
                          color: AppColors.success.withValues(alpha: 0.1),
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: Text(
                          med.statusLabel,
                          style: AppTypography.bodySmall
                              .copyWith(color: AppColors.success),
                        ),
                      ),
                      const SizedBox(width: AppSpacing.sm),
                      const Icon(Icons.chevron_right,
                          color: AppColors.textTertiary),
                    ],
                  ),
                ),
              ),
            ),
          ),
        ),
      ],
    );
  }

  Future<void> _scanMedicineQR() async {
    final result = await Navigator.push<MedicineItem>(
      context,
      MaterialPageRoute(builder: (_) => const _ScanMedicineDialog()),
    );
    if (result != null && mounted) {
      setState(() {
        _selectedMedicine = result;
        _step = 1;
      });
    }
  }

  // ── Step 1: Enter Customer ────────────────────────────────────────────────

  Widget _buildEnterCustomer() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Selected medicine card
        Container(
          padding: const EdgeInsets.all(AppSpacing.md),
          decoration: AppDecorations.gradientCard(
              [const Color(0xFF6366F1), const Color(0xFF4F46E5)]),
          child: Row(
            children: [
              const Icon(Icons.medication_outlined,
                  color: Colors.white, size: 28),
              const SizedBox(width: AppSpacing.md),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Medicine #${_selectedMedicine!.id}',
                      style: AppTypography.titleMedium
                          .copyWith(color: Colors.white),
                    ),
                    Text(
                      'Batch: ${_selectedMedicine!.batchNumber ?? _selectedMedicine!.batchId}',
                      style: AppTypography.bodySmall.copyWith(
                          color: Colors.white.withValues(alpha: 0.8)),
                    ),
                  ],
                ),
              ),
              TextButton(
                onPressed: () => setState(() => _step = 0),
                child: Text('Change',
                    style: TextStyle(
                        color: Colors.white.withValues(alpha: 0.9))),
              ),
            ],
          ),
        ),

        const SizedBox(height: AppSpacing.lg),

        Text('Customer Details', style: AppTypography.titleLarge),
        const SizedBox(height: AppSpacing.md),

        // Customer name (optional)
        TextField(
          controller: _customerNameController,
          decoration: const InputDecoration(
            labelText: 'Customer Name (optional)',
            prefixIcon: Icon(Icons.person_outline, size: 20),
          ),
        ),

        const SizedBox(height: AppSpacing.md),

        // Customer wallet address
        TextField(
          controller: _customerController,
          decoration: InputDecoration(
            labelText: 'Customer Wallet Address',
            hintText: '0x...',
            prefixIcon: const Icon(Icons.account_balance_wallet_outlined,
                size: 20),
            suffixIcon: IconButton(
              icon: const Icon(Icons.qr_code_scanner, size: 20),
              onPressed: _scanCustomerAddress,
              tooltip: 'Scan QR',
            ),
          ),
          maxLines: 1,
        ),

        const SizedBox(height: AppSpacing.md),

        // Info note
        Container(
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(
            color: const Color(0xFFEFF6FF),
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: const Color(0xFFBFDBFE)),
          ),
          child: Row(
            children: [
              Icon(Icons.info_outline, color: Colors.blue.shade700, size: 18),
              const SizedBox(width: AppSpacing.sm),
              Expanded(
                child: Text(
                  'Ownership will be transferred on the blockchain. This action cannot be undone.',
                  style: AppTypography.bodySmall
                      .copyWith(color: Colors.blue.shade900),
                ),
              ),
            ],
          ),
        ),

        if (_error != null) ...[
          const SizedBox(height: AppSpacing.md),
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: const Color(0xFFFEF2F2),
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: const Color(0xFFFECACA)),
            ),
            child: Row(
              children: [
                const Icon(Icons.error_outline,
                    color: AppColors.error, size: 18),
                const SizedBox(width: AppSpacing.sm),
                Expanded(
                  child: Text(_error!,
                      style: AppTypography.bodySmall
                          .copyWith(color: AppColors.error)),
                ),
              ],
            ),
          ),
        ],

        const SizedBox(height: AppSpacing.lg),

        Row(
          children: [
            Expanded(
              child: OutlinedButton(
                onPressed: () => setState(() => _step = 0),
                child: const Text('Back'),
              ),
            ),
            const SizedBox(width: AppSpacing.md),
            Expanded(
              flex: 2,
              child: ElevatedButton(
                onPressed: _validateAndProceed,
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppColors.primary,
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(vertical: 14),
                ),
                child: const Text('Review Sale'),
              ),
            ),
          ],
        ),
      ],
    );
  }

  Future<void> _scanCustomerAddress() async {
    final address = await Navigator.push<String>(
      context,
      MaterialPageRoute(builder: (_) => const _ScanAddressDialog()),
    );
    if (address != null) {
      _customerController.text = address;
    }
  }

  void _validateAndProceed() {
    final addr = _customerController.text.trim();
    if (addr.isEmpty) {
      setState(() => _error = 'Please enter customer wallet address');
      return;
    }
    if (!addr.startsWith('0x') || addr.length != 42) {
      setState(() => _error = 'Invalid Ethereum address (must be 0x + 40 hex chars)');
      return;
    }

    setState(() {
      _error = null;
      _step = 2;
    });
  }

  // ── Step 2: Confirm ───────────────────────────────────────────────────────

  Widget _buildConfirm() {
    final custAddr = _customerController.text.trim();
    final shortCust = '${custAddr.substring(0, 6)}...${custAddr.substring(custAddr.length - 4)}';

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text('Confirm Sale', style: AppTypography.displayMedium),
        const SizedBox(height: AppSpacing.lg),

        Container(
          padding: const EdgeInsets.all(AppSpacing.lg),
          decoration: AppDecorations.elevatedCard,
          child: Column(
            children: [
              _ConfirmRow(
                label: 'Medicine ID',
                value: '#${_selectedMedicine!.id}',
              ),
              const Divider(height: 24),
              _ConfirmRow(
                label: 'Batch',
                value:
                    '${_selectedMedicine!.batchNumber ?? _selectedMedicine!.batchId}',
              ),
              const Divider(height: 24),
              _ConfirmRow(
                label: 'Customer',
                value: _customerNameController.text.trim().isNotEmpty
                    ? _customerNameController.text.trim()
                    : shortCust,
              ),
              const Divider(height: 24),
              _ConfirmRow(label: 'Customer Address', value: shortCust),
              const Divider(height: 24),
              _ConfirmRow(label: 'Action', value: 'Transfer Ownership'),
            ],
          ),
        ),

        if (_error != null) ...[
          const SizedBox(height: AppSpacing.md),
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: const Color(0xFFFEF2F2),
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: const Color(0xFFFECACA)),
            ),
            child: Text(_error!,
                style:
                    AppTypography.bodySmall.copyWith(color: AppColors.error)),
          ),
        ],

        const SizedBox(height: AppSpacing.xl),

        Row(
          children: [
            Expanded(
              child: OutlinedButton(
                onPressed: _isTransferring ? null : () => setState(() => _step = 1),
                child: const Text('Back'),
              ),
            ),
            const SizedBox(width: AppSpacing.md),
            Expanded(
              flex: 2,
              child: SizedBox(
                height: 50,
                child: Container(
                  decoration: BoxDecoration(
                    gradient: _isTransferring ? null : AppGradients.success,
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: ElevatedButton.icon(
                    onPressed: _isTransferring ? null : _executeTransfer,
                    icon: _isTransferring
                        ? const SizedBox(
                            width: 20,
                            height: 20,
                            child: CircularProgressIndicator(
                                strokeWidth: 2, color: Colors.white),
                          )
                        : const Icon(Icons.send),
                    label: Text(_isTransferring
                        ? 'Processing...'
                        : 'Confirm & Transfer'),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.transparent,
                      shadowColor: Colors.transparent,
                      foregroundColor: Colors.white,
                      disabledBackgroundColor: AppColors.border,
                    ),
                  ),
                ),
              ),
            ),
          ],
        ),
      ],
    );
  }

  Future<void> _executeTransfer() async {
    setState(() {
      _isTransferring = true;
      _error = null;
    });

    try {
      final blockchain = context.read<BlockchainService>();
      final inventory = context.read<InventoryService>();
      final custAddr = _customerController.text.trim();

      // 1. Transfer custody on-chain
      final txHash = await blockchain.transferCustody(
        medicineId: _selectedMedicine!.id,
        toAddress: custAddr,
      );

      // 2. Log scan (pharmacy location — using 0,0 as placeholder)
      try {
        await blockchain.logScan(
          medicineId: _selectedMedicine!.id,
          latitude: 0,
          longitude: 0,
          location: 'Pharmacy POS',
          deviceId: 'pharmacy_app',
        );
      } catch (_) {
        // Scan logging is best-effort; transfer is the critical operation
      }

      // 3. Record sale locally
      inventory.recordSale(SaleRecord(
        medicineId: _selectedMedicine!.id,
        batchId: _selectedMedicine!.batchId,
        customerAddress: custAddr,
        txHash: txHash,
        timestamp: DateTime.now(),
        batchNumber: _selectedMedicine!.batchNumber,
        customerName: _customerNameController.text.trim().isNotEmpty
            ? _customerNameController.text.trim()
            : null,
      ));

      _txHash = txHash;
      setState(() => _step = 3);
    } catch (e) {
      setState(() {
        _error = 'Transfer failed: $e';
        _isTransferring = false;
      });
    }
  }

  // ── Step 3: Done ──────────────────────────────────────────────────────────

  Widget _buildDone() {
    final shortTx = _txHash != null && _txHash!.length > 14
        ? '${_txHash!.substring(0, 10)}...${_txHash!.substring(_txHash!.length - 4)}'
        : _txHash ?? '';

    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Container(
            width: 100,
            height: 100,
            decoration: BoxDecoration(
              color: AppColors.success.withValues(alpha: 0.1),
              shape: BoxShape.circle,
            ),
            child: const Icon(Icons.check_circle,
                size: 64, color: AppColors.success),
          )
              .animate()
              .scaleXY(
                  begin: 0.3, end: 1, duration: 600.ms,
                  curve: Curves.easeOutBack),

          const SizedBox(height: AppSpacing.lg),

          Text('Sale Complete!', style: AppTypography.displayMedium)
              .animate()
              .fadeIn(duration: 400.ms, delay: 300.ms),

          const SizedBox(height: AppSpacing.md),

          Container(
            padding: const EdgeInsets.all(AppSpacing.md),
            decoration: BoxDecoration(
              color: AppColors.success.withValues(alpha: 0.05),
              borderRadius: BorderRadius.circular(12),
              border: Border.all(
                  color: AppColors.success.withValues(alpha: 0.2)),
            ),
            child: Column(
              children: [
                Text('Ownership transferred successfully',
                    style: AppTypography.bodyLarge),
                const SizedBox(height: AppSpacing.sm),
                Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Text('Tx: ', style: AppTypography.bodySmall),
                    Text(shortTx, style: AppTypography.mono),
                    const SizedBox(width: 4),
                    InkWell(
                      onTap: () {
                        Clipboard.setData(ClipboardData(text: _txHash ?? ''));
                        ScaffoldMessenger.of(context).showSnackBar(
                          const SnackBar(
                              content: Text('Transaction hash copied')),
                        );
                      },
                      child: const Icon(Icons.copy, size: 16,
                          color: AppColors.textTertiary),
                    ),
                  ],
                ),
              ],
            ),
          ).animate().fadeIn(duration: 400.ms, delay: 500.ms),

          const SizedBox(height: AppSpacing.xl),

          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              OutlinedButton.icon(
                onPressed: () => Navigator.pop(context),
                icon: const Icon(Icons.arrow_back),
                label: const Text('Back to Dashboard'),
              ),
              const SizedBox(width: AppSpacing.md),
              ElevatedButton.icon(
                onPressed: () {
                  setState(() {
                    _step = 0;
                    _selectedMedicine = null;
                    _customerController.clear();
                    _customerNameController.clear();
                    _error = null;
                    _txHash = null;
                    _isTransferring = false;
                  });
                },
                icon: const Icon(Icons.sell_outlined),
                label: const Text('Sell Another'),
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppColors.primary,
                  foregroundColor: Colors.white,
                ),
              ),
            ],
          ).animate().fadeIn(duration: 400.ms, delay: 700.ms),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Sell Medicine'),
        centerTitle: true,
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(AppSpacing.lg),
          child: AnimatedSwitcher(
            duration: const Duration(milliseconds: 300),
            child: KeyedSubtree(
              key: ValueKey(_step),
              child: switch (_step) {
                0 => _buildSelectMedicine(),
                1 => _buildEnterCustomer(),
                2 => _buildConfirm(),
                3 => _buildDone(),
                _ => const SizedBox.shrink(),
              },
            ),
          ),
        ),
      ),
    );
  }
}

// ── Confirm Row ─────────────────────────────────────────────────────────────

class _ConfirmRow extends StatelessWidget {
  final String label;
  final String value;

  const _ConfirmRow({required this.label, required this.value});

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Text(label, style: AppTypography.bodyMedium),
        Flexible(
          child: Text(value,
              style: AppTypography.titleSmall, textAlign: TextAlign.end),
        ),
      ],
    );
  }
}

// ── Scan Medicine QR (picks a medicine from QR) ─────────────────────────────

class _ScanMedicineDialog extends StatefulWidget {
  const _ScanMedicineDialog();

  @override
  State<_ScanMedicineDialog> createState() => _ScanMedicineDialogState();
}

class _ScanMedicineDialogState extends State<_ScanMedicineDialog> {
  final MobileScannerController _ctrl = MobileScannerController();
  bool _processing = false;

  @override
  void dispose() {
    _ctrl.dispose();
    super.dispose();
  }

  Future<void> _onDetect(BarcodeCapture capture) async {
    if (_processing) return;
    final barcode = capture.barcodes.firstOrNull;
    if (barcode?.rawValue == null) return;

    setState(() => _processing = true);
    await _ctrl.stop();

    try {
      final data = jsonDecode(barcode!.rawValue!);
      final medicineId = data['id'] as int?;

      if (medicineId == null) throw Exception('Invalid QR');

      final blockchain = context.read<BlockchainService>();
      final wallet = context.read<WalletService>();

      final medicine = await blockchain.getMedicine(medicineId);
      if (medicine == null) throw Exception('Medicine not found on chain');

      if (medicine.currentOwner.toLowerCase() !=
          wallet.address!.toLowerCase()) {
        throw Exception('You are not the current owner');
      }

      if (!medicine.isAtPharmacy) {
        throw Exception('Medicine status is "${medicine.statusLabel}", not "At Pharmacy"');
      }

      final batch = await blockchain.getBatch(medicine.batchId);
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

      if (mounted) Navigator.pop(context, enriched);
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error: $e'), backgroundColor: AppColors.error),
        );
        setState(() => _processing = false);
        _ctrl.start();
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Scan Medicine')),
      body: Stack(
        children: [
          MobileScanner(controller: _ctrl, onDetect: _onDetect),
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
          if (_processing)
            Container(
              color: Colors.black54,
              child: const Center(
                child: CircularProgressIndicator(color: Colors.white),
              ),
            ),
        ],
      ),
    );
  }
}

// ── Scan Customer Address QR ────────────────────────────────────────────────

class _ScanAddressDialog extends StatefulWidget {
  const _ScanAddressDialog();

  @override
  State<_ScanAddressDialog> createState() => _ScanAddressDialogState();
}

class _ScanAddressDialogState extends State<_ScanAddressDialog> {
  final MobileScannerController _ctrl = MobileScannerController();
  bool _processing = false;

  @override
  void dispose() {
    _ctrl.dispose();
    super.dispose();
  }

  void _onDetect(BarcodeCapture capture) {
    if (_processing) return;
    final barcode = capture.barcodes.firstOrNull;
    if (barcode?.rawValue == null) return;

    final raw = barcode!.rawValue!.trim();
    // Accept raw Ethereum address or JSON with address field
    String? addr;
    if (raw.startsWith('0x') && raw.length == 42) {
      addr = raw;
    } else {
      try {
        final data = jsonDecode(raw);
        addr = data['address'] as String?;
      } catch (_) {}
    }

    if (addr != null && addr.startsWith('0x') && addr.length == 42) {
      setState(() => _processing = true);
      _ctrl.stop();
      Navigator.pop(context, addr);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Scan Customer Address')),
      body: Stack(
        children: [
          MobileScanner(controller: _ctrl, onDetect: _onDetect),
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
                  'Scan customer wallet QR code',
                  style:
                      AppTypography.bodyMedium.copyWith(color: Colors.white),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
