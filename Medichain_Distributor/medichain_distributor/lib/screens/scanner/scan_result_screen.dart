import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:provider/provider.dart';
import '../../config/app_config.dart';
import '../../models/batch_model.dart';
import '../../services/blockchain_service.dart';
import '../../services/scanner_service.dart';
import '../../services/location_service.dart';
import '../../services/cache_service.dart';
import '../../services/private_key_wallet_service.dart';
import '../../theme/app_theme.dart';
import '../../widgets/page_route.dart';
import '../batch/batch_detail_screen.dart';

class ScanResultScreen extends StatefulWidget {
  final int batchId;
  final String batchNumber;
  final int totalUnits;
  final Map<String, dynamic> qrData;

  const ScanResultScreen({
    super.key,
    required this.batchId,
    required this.batchNumber,
    required this.totalUnits,
    required this.qrData,
  });

  @override
  State<ScanResultScreen> createState() => _ScanResultScreenState();
}

class _ScanResultScreenState extends State<ScanResultScreen> {
  BatchModel? _batch;
  List<int> _medicineIds = [];
  bool _isLoading = true;
  bool _isScanning = false;
  bool _scanComplete = false;
  String? _error;
  String _locationText = 'Acquiring GPS...';
  double? _latitude;
  double? _longitude;
  String? _txHash;

  @override
  void initState() {
    super.initState();
    _loadBatchData();
    _acquireLocation();
  }

  Future<void> _loadBatchData() async {
    try {
      final blockchainService = context.read<BlockchainService>();
      final cacheService = context.read<CacheService>();

      // Check cache first
      final cached = await cacheService.get('batch_${widget.batchId}');
      if (cached != null) {
        _batch = BatchModel.fromJson(cached);
        _medicineIds = _batch!.medicineIds;
      }

      // Always fetch fresh from blockchain
      final batch = await blockchainService.getBatch(widget.batchId);
      final medicineIds = await blockchainService.getBatchMedicines(widget.batchId);

      if (batch != null && mounted) {
        final updatedBatch = BatchModel(
          batchId: batch.batchId,
          batchNumber: batch.batchNumber,
          ipfsHash: batch.ipfsHash,
          manufacturer: batch.manufacturer,
          totalUnits: batch.totalUnits,
          registeredUnits: batch.registeredUnits,
          createdAt: batch.createdAt,
          isComplete: batch.isComplete,
          medicineIds: medicineIds,
        );

        // Cache the result
        await cacheService.set('batch_${widget.batchId}', updatedBatch.toJson());

        setState(() {
          _batch = updatedBatch;
          _medicineIds = medicineIds;
          _isLoading = false;
        });
      } else if (mounted) {
        setState(() {
          _error = 'Batch #${widget.batchId} not found on blockchain';
          _isLoading = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _error = 'Failed to load batch: $e';
          _isLoading = false;
        });
      }
    }
  }

  Future<void> _acquireLocation() async {
    final locationService = context.read<LocationService>();
    final result = await locationService.getLocationWithAddress();

    if (result != null && mounted) {
      setState(() {
        _latitude = result.position.latitude;
        _longitude = result.position.longitude;
        _locationText = result.address;
      });
    } else if (mounted) {
      setState(() => _locationText = 'GPS unavailable');
    }
  }

  Future<void> _logScanOnBlockchain() async {
    if (_medicineIds.isEmpty || _latitude == null || _longitude == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(_medicineIds.isEmpty ? 'No medicines in batch' : 'GPS not available yet'),
          backgroundColor: AppColors.warning,
        ),
      );
      return;
    }

    setState(() => _isScanning = true);
    HapticFeedback.mediumImpact();

    try {
      final scannerService = context.read<ScannerService>();
      final cacheService = context.read<CacheService>();
      final walletService = context.read<PrivateKeyWalletService>();

      // Use batch scan (max 50 medicines per call)
      final idsToScan = _medicineIds.length > 50 ? _medicineIds.sublist(0, 50) : _medicineIds;

      final txHash = await scannerService.logBatchScan(
        medicineIds: idsToScan,
        latitude: _latitude!,
        longitude: _longitude!,
        location: _locationText,
        deviceId: 'dist_${walletService.address?.substring(0, 8) ?? "unknown"}',
      );

      // Add to recent scans cache
      await cacheService.addRecentScan(widget.batchId);

      if (mounted) {
        setState(() {
          _txHash = txHash;
          _scanComplete = true;
          _isScanning = false;
        });
        HapticFeedback.heavyImpact();
      }
    } catch (e) {
      if (mounted) {
        setState(() => _isScanning = false);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Scan failed: $e'),
            backgroundColor: AppColors.error,
          ),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        title: const Text('Scan Result'),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () => Navigator.of(context).pop(),
        ),
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator(color: AppColors.primary))
          : _error != null
              ? Center(
                  child: Padding(
                    padding: const EdgeInsets.all(32),
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        const Icon(Icons.error_outline, size: 64, color: AppColors.error),
                        const SizedBox(height: 16),
                        Text(_error!, style: AppTypography.bodyLarge, textAlign: TextAlign.center),
                        const SizedBox(height: 24),
                        ElevatedButton(
                          onPressed: () => Navigator.of(context).pop(),
                          child: const Text('Go Back'),
                        ),
                      ],
                    ),
                  ),
                )
              : SingleChildScrollView(
                  padding: const EdgeInsets.all(AppSpacing.md),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      // Success Animation
                      if (_scanComplete)
                        Container(
                          width: double.infinity,
                          padding: const EdgeInsets.all(20),
                          decoration: AppDecorations.gradientCard(
                            [AppColors.primaryGradientStart, AppColors.primaryGradientEnd],
                          ),
                          child: Column(
                            children: [
                              const Icon(Icons.check_circle_outline, color: Colors.white, size: 48),
                              const SizedBox(height: 12),
                              Text(
                                'Scan Logged on Blockchain!',
                                style: AppTypography.titleLarge.copyWith(color: Colors.white),
                              ),
                              const SizedBox(height: 4),
                              Text(
                                'Tx: ${_txHash?.substring(0, 10)}...${_txHash?.substring(_txHash!.length - 6)}',
                                style: AppTypography.mono.copyWith(color: Colors.white70, fontSize: 11),
                              ),
                            ],
                          ),
                        )
                            .animate()
                            .fadeIn(duration: 600.ms)
                            .scaleXY(begin: 0.9, end: 1.0, duration: 600.ms, curve: Curves.easeOutBack),

                      if (_scanComplete) const SizedBox(height: AppSpacing.md),

                      // Batch Info Card
                      Container(
                        padding: const EdgeInsets.all(AppSpacing.md),
                        decoration: AppDecorations.card,
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(
                              children: [
                                Container(
                                  width: 44,
                                  height: 44,
                                  decoration: BoxDecoration(
                                    color: AppColors.primaryLight,
                                    borderRadius: BorderRadius.circular(12),
                                  ),
                                  child: const Icon(Icons.inventory_2, color: AppColors.primary, size: 22),
                                ),
                                const SizedBox(width: 12),
                                Expanded(
                                  child: Column(
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    children: [
                                      Text('Batch #${widget.batchId}', style: AppTypography.titleMedium),
                                      Text(widget.batchNumber, style: AppTypography.bodySmall),
                                    ],
                                  ),
                                ),
                                Container(
                                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                                  decoration: BoxDecoration(
                                    color: _batch?.isComplete == true
                                        ? AppColors.primaryLight
                                        : const Color(0xFFFEF3C7),
                                    borderRadius: BorderRadius.circular(8),
                                  ),
                                  child: Text(
                                    _batch?.isComplete == true ? 'Complete' : 'Pending',
                                    style: AppTypography.bodySmall.copyWith(
                                      color: _batch?.isComplete == true
                                          ? AppColors.primaryDark
                                          : const Color(0xFF92400E),
                                      fontWeight: FontWeight.w600,
                                    ),
                                  ),
                                ),
                              ],
                            ),
                            const SizedBox(height: 16),
                            const Divider(height: 1, color: AppColors.borderLight),
                            const SizedBox(height: 12),
                            _DetailRow(label: 'Medicines', value: '${_medicineIds.length} units'),
                            _DetailRow(label: 'Total Units', value: '${_batch?.totalUnits ?? widget.totalUnits}'),
                            _DetailRow(label: 'Registered', value: '${_batch?.registeredUnits ?? 0}'),
                            _DetailRow(
                              label: 'Manufacturer',
                              value: _batch?.manufacturer != null
                                  ? '${_batch!.manufacturer.substring(0, 8)}...${_batch!.manufacturer.substring(_batch!.manufacturer.length - 6)}'
                                  : 'Loading...',
                            ),
                          ],
                        ),
                      )
                          .animate()
                          .fadeIn(duration: 500.ms, delay: 100.ms)
                          .slideY(begin: 0.05, end: 0, duration: 500.ms),

                      const SizedBox(height: 12),

                      // Location Card
                      Container(
                        padding: const EdgeInsets.all(AppSpacing.md),
                        decoration: AppDecorations.card,
                        child: Row(
                          children: [
                            Container(
                              width: 40,
                              height: 40,
                              decoration: BoxDecoration(
                                color: const Color(0xFFEDE9FE),
                                borderRadius: BorderRadius.circular(10),
                              ),
                              child: Icon(
                                _latitude != null ? Icons.location_on : Icons.location_searching,
                                color: const Color(0xFF7C3AED),
                                size: 20,
                              ),
                            ),
                            const SizedBox(width: 12),
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text('GPS Location', style: AppTypography.titleSmall),
                                  const SizedBox(height: 2),
                                  Text(_locationText, style: AppTypography.bodySmall),
                                  if (_latitude != null)
                                    Text(
                                      '${_latitude!.toStringAsFixed(6)}, ${_longitude!.toStringAsFixed(6)}',
                                      style: AppTypography.mono.copyWith(fontSize: 11),
                                    ),
                                ],
                              ),
                            ),
                            if (_latitude == null)
                              const SizedBox(
                                width: 20,
                                height: 20,
                                child: CircularProgressIndicator(strokeWidth: 2, color: Color(0xFF7C3AED)),
                              ),
                          ],
                        ),
                      )
                          .animate()
                          .fadeIn(duration: 500.ms, delay: 200.ms)
                          .slideY(begin: 0.05, end: 0, duration: 500.ms),

                      const SizedBox(height: AppSpacing.lg),

                      // Action Buttons
                      if (!_scanComplete)
                        SizedBox(
                          width: double.infinity,
                          height: 52,
                          child: Container(
                            decoration: BoxDecoration(
                              gradient: _isScanning ? null : AppGradients.primary,
                              borderRadius: BorderRadius.circular(14),
                              boxShadow: _isScanning
                                  ? null
                                  : [
                                      BoxShadow(
                                        color: AppColors.primary.withValues(alpha: 0.3),
                                        blurRadius: 12,
                                        offset: const Offset(0, 4),
                                      ),
                                    ],
                            ),
                            child: ElevatedButton.icon(
                              onPressed: _isScanning ? null : _logScanOnBlockchain,
                              icon: _isScanning
                                  ? const SizedBox(
                                      width: 18,
                                      height: 18,
                                      child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                                    )
                                  : const Icon(Icons.upload_rounded),
                              label: Text(_isScanning ? 'Logging on blockchain...' : 'Log Scan on Blockchain'),
                              style: ElevatedButton.styleFrom(
                                backgroundColor: Colors.transparent,
                                shadowColor: Colors.transparent,
                                disabledBackgroundColor: AppColors.border,
                              ),
                            ),
                          ),
                        )
                            .animate()
                            .fadeIn(duration: 500.ms, delay: 300.ms)
                            .slideY(begin: 0.1, end: 0, duration: 500.ms),

                      if (_scanComplete) ...[
                        SizedBox(
                          width: double.infinity,
                          height: 52,
                          child: ElevatedButton.icon(
                            onPressed: () {
                              Navigator.of(context).pushReplacement(
                                FadeSlideRoute(
                                  page: BatchDetailScreen(
                                    batchId: widget.batchId,
                                    medicineIds: _medicineIds,
                                  ),
                                ),
                              );
                            },
                            icon: const Icon(Icons.visibility_outlined),
                            label: const Text('View Batch Details'),
                            style: ElevatedButton.styleFrom(
                              backgroundColor: AppColors.primary,
                            ),
                          ),
                        )
                            .animate()
                            .fadeIn(duration: 500.ms, delay: 200.ms),

                        const SizedBox(height: 12),

                        SizedBox(
                          width: double.infinity,
                          height: 52,
                          child: OutlinedButton.icon(
                            onPressed: () => Navigator.of(context).pop(),
                            icon: const Icon(Icons.qr_code_scanner),
                            label: const Text('Scan Another'),
                          ),
                        )
                            .animate()
                            .fadeIn(duration: 500.ms, delay: 300.ms),
                      ],

                      const SizedBox(height: AppSpacing.xxl),
                    ],
                  ),
                ),
    );
  }
}

class _DetailRow extends StatelessWidget {
  final String label;
  final String value;

  const _DetailRow({required this.label, required this.value});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: AppTypography.bodySmall),
          Text(value, style: AppTypography.bodyMedium.copyWith(color: AppColors.textPrimary)),
        ],
      ),
    );
  }
}
