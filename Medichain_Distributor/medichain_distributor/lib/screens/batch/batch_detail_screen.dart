import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:provider/provider.dart';
import '../../config/app_config.dart';
import '../../models/batch_model.dart';
import '../../models/medicine_model.dart';
import '../../services/blockchain_service.dart';
import '../../services/cache_service.dart';
import '../../theme/app_theme.dart';
import '../../widgets/page_route.dart';
import 'medicine_detail_screen.dart';
import '../transfer/transfer_screen.dart';

class BatchDetailScreen extends StatefulWidget {
  final int batchId;
  final List<int> medicineIds;

  const BatchDetailScreen({
    super.key,
    required this.batchId,
    this.medicineIds = const [],
  });

  @override
  State<BatchDetailScreen> createState() => _BatchDetailScreenState();
}

class _BatchDetailScreenState extends State<BatchDetailScreen> {
  BatchModel? _batch;
  final List<MedicineModel> _medicines = [];
  bool _isLoading = true;
  String? _manufacturerName;

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  Future<void> _loadData() async {
    setState(() => _isLoading = true);

    try {
      final blockchainService = context.read<BlockchainService>();
      final cacheService = context.read<CacheService>();

      // Load batch
      final batch = await blockchainService.getBatch(widget.batchId);
      if (batch == null) {
        if (mounted) setState(() => _isLoading = false);
        return;
      }

      // Get medicine IDs
      List<int> medicineIds = widget.medicineIds;
      if (medicineIds.isEmpty) {
        medicineIds = await blockchainService.getBatchMedicines(widget.batchId);
      }

      // Load medicines (first 20)
      final meds = <MedicineModel>[];
      final limit = medicineIds.length > 20 ? 20 : medicineIds.length;
      for (int i = 0; i < limit; i++) {
        // Check cache first
        final cached = await cacheService.get('med_${medicineIds[i]}');
        if (cached != null) {
          meds.add(MedicineModel.fromJson(cached));
        } else {
          final med = await blockchainService.getMedicine(medicineIds[i]);
          if (med != null) {
            meds.add(med);
            await cacheService.set('med_${medicineIds[i]}', med.toJson());
          }
        }
      }

      // Load manufacturer name
      final actorInfo = await blockchainService.getActorInfo(batch.manufacturer);

      if (mounted) {
        setState(() {
          _batch = BatchModel(
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
          _medicines.addAll(meds);
          _manufacturerName = actorInfo?['name'] ?? 'Unknown';
          _isLoading = false;
        });
      }
    } catch (e) {
      if (mounted) setState(() => _isLoading = false);
      debugPrint('Load batch detail error: $e');
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        title: Text('Batch #${widget.batchId}'),
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator(color: AppColors.primary))
          : _batch == null
              ? const Center(child: Text('Batch not found'))
              : RefreshIndicator(
                  onRefresh: _loadData,
                  child: ListView(
                    padding: const EdgeInsets.all(AppSpacing.md),
                    children: [
                      // Batch header
                      Container(
                        padding: const EdgeInsets.all(AppSpacing.md),
                        decoration: AppDecorations.gradientCard(
                          [AppColors.primaryGradientStart, AppColors.primaryGradientEnd],
                        ),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(
                              children: [
                                const Icon(Icons.inventory_2, color: Colors.white, size: 28),
                                const SizedBox(width: 12),
                                Expanded(
                                  child: Column(
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    children: [
                                      Text(
                                        _batch!.batchNumber,
                                        style: AppTypography.titleLarge.copyWith(color: Colors.white),
                                      ),
                                      Text(
                                        'ID: ${_batch!.batchId}',
                                        style: AppTypography.bodySmall.copyWith(color: Colors.white70),
                                      ),
                                    ],
                                  ),
                                ),
                              ],
                            ),
                            const SizedBox(height: 16),
                            Row(
                              children: [
                                _BatchStat(label: 'Total', value: '${_batch!.totalUnits}'),
                                _BatchStat(label: 'Registered', value: '${_batch!.registeredUnits}'),
                                _BatchStat(label: 'Status', value: _batch!.isComplete ? 'Complete' : 'Pending'),
                              ],
                            ),
                          ],
                        ),
                      )
                          .animate()
                          .fadeIn(duration: 500.ms)
                          .slideY(begin: 0.05, end: 0, duration: 500.ms),

                      const SizedBox(height: 12),

                      // Manufacturer info
                      Container(
                        padding: const EdgeInsets.all(AppSpacing.md),
                        decoration: AppDecorations.card,
                        child: Row(
                          children: [
                            Container(
                              width: 40,
                              height: 40,
                              decoration: BoxDecoration(
                                color: const Color(0xFFE0E7FF),
                                borderRadius: BorderRadius.circular(10),
                              ),
                              child: const Icon(Icons.factory, color: Color(0xFF4F46E5), size: 20),
                            ),
                            const SizedBox(width: 12),
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text('Manufacturer', style: AppTypography.bodySmall),
                                  Text(_manufacturerName ?? 'Loading...', style: AppTypography.titleSmall),
                                  Text(
                                    '${_batch!.manufacturer.substring(0, 8)}...${_batch!.manufacturer.substring(_batch!.manufacturer.length - 6)}',
                                    style: AppTypography.mono.copyWith(fontSize: 11),
                                  ),
                                ],
                              ),
                            ),
                          ],
                        ),
                      )
                          .animate()
                          .fadeIn(duration: 500.ms, delay: 100.ms),

                      const SizedBox(height: AppSpacing.lg),

                      // Transfer button
                      SizedBox(
                        width: double.infinity,
                        height: 50,
                        child: ElevatedButton.icon(
                          onPressed: _medicines.isEmpty
                              ? null
                              : () {
                                  HapticFeedback.lightImpact();
                                  Navigator.of(context).push(
                                    FadeSlideRoute(
                                      page: TransferScreen(
                                        batchId: widget.batchId,
                                        medicineIds: _batch!.medicineIds,
                                      ),
                                    ),
                                  );
                                },
                          icon: const Icon(Icons.send_rounded),
                          label: const Text('Transfer Batch'),
                          style: ElevatedButton.styleFrom(backgroundColor: AppColors.primary),
                        ),
                      )
                          .animate()
                          .fadeIn(duration: 500.ms, delay: 200.ms),

                      const SizedBox(height: AppSpacing.lg),

                      // Medicines list
                      Text(
                        'Medicines (${_medicines.length}${_batch!.medicineIds.length > 20 ? " of ${_batch!.medicineIds.length}" : ""})',
                        style: AppTypography.titleMedium,
                      )
                          .animate()
                          .fadeIn(duration: 500.ms, delay: 300.ms),
                      const SizedBox(height: 8),

                      ...List.generate(
                        _medicines.length,
                        (i) {
                          final med = _medicines[i];
                          return GestureDetector(
                            onTap: () {
                              Navigator.of(context).push(
                                FadeSlideRoute(page: MedicineDetailScreen(medicineId: med.id)),
                              );
                            },
                            child: Container(
                              margin: const EdgeInsets.only(bottom: 8),
                              padding: const EdgeInsets.all(14),
                              decoration: AppDecorations.card,
                              child: Row(
                                children: [
                                  Container(
                                    width: 36,
                                    height: 36,
                                    decoration: BoxDecoration(
                                      color: med.isFlagged
                                          ? const Color(0xFFFEE2E2)
                                          : AppColors.primaryLight,
                                      borderRadius: BorderRadius.circular(10),
                                    ),
                                    child: Icon(
                                      med.isFlagged ? Icons.warning : Icons.medication,
                                      size: 18,
                                      color: med.isFlagged ? AppColors.error : AppColors.primary,
                                    ),
                                  ),
                                  const SizedBox(width: 12),
                                  Expanded(
                                    child: Column(
                                      crossAxisAlignment: CrossAxisAlignment.start,
                                      children: [
                                        Text('Medicine #${med.id}', style: AppTypography.titleSmall),
                                        Text(
                                          AppConfig.statusName(med.status),
                                          style: AppTypography.bodySmall,
                                        ),
                                      ],
                                    ),
                                  ),
                                  Container(
                                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                                    decoration: BoxDecoration(
                                      color: _statusColor(med.status).withValues(alpha: 0.1),
                                      borderRadius: BorderRadius.circular(6),
                                    ),
                                    child: Text(
                                      AppConfig.statusName(med.status),
                                      style: AppTypography.bodySmall.copyWith(
                                        color: _statusColor(med.status),
                                        fontWeight: FontWeight.w600,
                                        fontSize: 11,
                                      ),
                                    ),
                                  ),
                                  const SizedBox(width: 4),
                                  const Icon(Icons.chevron_right, size: 18, color: AppColors.textTertiary),
                                ],
                              ),
                            ),
                          )
                              .animate()
                              .fadeIn(
                                duration: 400.ms,
                                delay: Duration(milliseconds: 400 + i * 60),
                              )
                              .slideX(begin: 0.03, end: 0, duration: 400.ms);
                        },
                      ),

                      const SizedBox(height: AppSpacing.xxl),
                    ],
                  ),
                ),
    );
  }

  Color _statusColor(int status) {
    switch (status) {
      case 0: return const Color(0xFF6B7280); // Manufactured
      case 1: return const Color(0xFF3B82F6); // InTransit
      case 2: return AppColors.primary; // AtDistributor
      case 3: return const Color(0xFF8B5CF6); // AtPharmacy
      case 4: return const Color(0xFF059669); // Dispensed
      case 5: return AppColors.error; // Flagged
      default: return AppColors.textSecondary;
    }
  }
}

class _BatchStat extends StatelessWidget {
  final String label;
  final String value;

  const _BatchStat({required this.label, required this.value});

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: Column(
        children: [
          Text(value, style: AppTypography.titleMedium.copyWith(color: Colors.white)),
          Text(label, style: AppTypography.bodySmall.copyWith(color: Colors.white70)),
        ],
      ),
    );
  }
}
