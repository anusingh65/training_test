import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';
import '../../config/app_config.dart';
import '../../models/medicine_model.dart';
import '../../models/custody_record_model.dart';
import '../../models/scan_record_model.dart';
import '../../services/blockchain_service.dart';
import '../../services/scanner_service.dart';
import '../../services/cache_service.dart';
import '../../theme/app_theme.dart';
import '../../widgets/page_route.dart';
import '../history/history_screen.dart';

class MedicineDetailScreen extends StatefulWidget {
  final int medicineId;

  const MedicineDetailScreen({super.key, required this.medicineId});

  @override
  State<MedicineDetailScreen> createState() => _MedicineDetailScreenState();
}

class _MedicineDetailScreenState extends State<MedicineDetailScreen> {
  MedicineModel? _medicine;
  List<CustodyRecordModel> _custodyHistory = [];
  List<ScanRecordModel> _scanHistory = [];
  bool _isLoading = true;
  final _dateFormat = DateFormat('dd MMM yyyy, HH:mm');

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  Future<void> _loadData() async {
    setState(() => _isLoading = true);

    try {
      final blockchainService = context.read<BlockchainService>();
      final scannerService = context.read<ScannerService>();
      final cacheService = context.read<CacheService>();

      // Load medicine
      final cached = await cacheService.get('med_${widget.medicineId}');
      MedicineModel? medicine;
      if (cached != null) {
        medicine = MedicineModel.fromJson(cached);
      } else {
        medicine = await blockchainService.getMedicine(widget.medicineId);
        if (medicine != null) {
          await cacheService.set('med_${widget.medicineId}', medicine.toJson());
        }
      }

      // Load custody history
      final custody = await blockchainService.getCustodyHistory(widget.medicineId);

      // Resolve actor names for custody records
      final resolvedCustody = <CustodyRecordModel>[];
      for (final record in custody) {
        final cachedActor = await cacheService.get('actor_${record.address}');
        if (cachedActor != null) {
          resolvedCustody.add(record.copyWith(
            name: cachedActor['name'],
            location: cachedActor['location'],
            role: cachedActor['role'],
          ));
        } else {
          final actorInfo = await blockchainService.getActorInfo(record.address);
          if (actorInfo != null) {
            await cacheService.set('actor_${record.address}', actorInfo);
            resolvedCustody.add(record.copyWith(
              name: actorInfo['name'],
              location: actorInfo['location'],
              role: actorInfo['role'],
            ));
          } else {
            resolvedCustody.add(record);
          }
        }
      }

      // Load scan history
      final scans = await scannerService.getScanHistory(widget.medicineId);

      if (mounted) {
        setState(() {
          _medicine = medicine;
          _custodyHistory = resolvedCustody;
          _scanHistory = scans;
          _isLoading = false;
        });
      }
    } catch (e) {
      if (mounted) setState(() => _isLoading = false);
      debugPrint('Load medicine detail error: $e');
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        title: Text('Medicine #${widget.medicineId}'),
        actions: [
          IconButton(
            icon: const Icon(Icons.history),
            onPressed: () {
              Navigator.of(context).push(
                FadeSlideRoute(page: HistoryScreen(medicineId: widget.medicineId)),
              );
            },
          ),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator(color: AppColors.primary))
          : _medicine == null
              ? const Center(child: Text('Medicine not found'))
              : RefreshIndicator(
                  onRefresh: _loadData,
                  child: ListView(
                    padding: const EdgeInsets.all(AppSpacing.md),
                    children: [
                      // Status card
                      Container(
                        padding: const EdgeInsets.all(AppSpacing.md),
                        decoration: AppDecorations.gradientCard(
                          _medicine!.isFlagged
                              ? [const Color(0xFFEF4444), const Color(0xFFDC2626)]
                              : [AppColors.primaryGradientStart, AppColors.primaryGradientEnd],
                        ),
                        child: Row(
                          children: [
                            Icon(
                              _medicine!.isFlagged ? Icons.warning : Icons.medication,
                              color: Colors.white,
                              size: 36,
                            ),
                            const SizedBox(width: 16),
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text(
                                    'Medicine #${_medicine!.id}',
                                    style: AppTypography.titleLarge.copyWith(color: Colors.white),
                                  ),
                                  Text(
                                    AppConfig.statusName(_medicine!.status),
                                    style: AppTypography.bodyMedium.copyWith(color: Colors.white70),
                                  ),
                                ],
                              ),
                            ),
                            if (_medicine!.isFlagged)
                              Container(
                                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                                decoration: BoxDecoration(
                                  color: Colors.white.withValues(alpha: 0.2),
                                  borderRadius: BorderRadius.circular(8),
                                ),
                                child: Text(
                                  'FLAGGED',
                                  style: AppTypography.labelLarge.copyWith(color: Colors.white, fontSize: 11),
                                ),
                              ),
                          ],
                        ),
                      )
                          .animate()
                          .fadeIn(duration: 500.ms)
                          .slideY(begin: 0.05, end: 0, duration: 500.ms),

                      const SizedBox(height: 12),

                      // Details card
                      Container(
                        padding: const EdgeInsets.all(AppSpacing.md),
                        decoration: AppDecorations.card,
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text('Details', style: AppTypography.titleSmall),
                            const SizedBox(height: 8),
                            _Row(label: 'Batch ID', value: '${_medicine!.batchId}'),
                            _Row(label: 'Status', value: AppConfig.statusName(_medicine!.status)),
                            _Row(label: 'Transfers', value: '${_medicine!.transferCount}'),
                            _Row(label: 'Scans', value: '${_medicine!.scanCount}'),
                            _Row(label: 'Flags', value: '${_medicine!.flagCount}'),
                            _Row(
                              label: 'Owner',
                              value: '${_medicine!.currentOwner.substring(0, 8)}...${_medicine!.currentOwner.substring(_medicine!.currentOwner.length - 6)}',
                            ),
                            _Row(
                              label: 'Manufacturer',
                              value: '${_medicine!.manufacturer.substring(0, 8)}...${_medicine!.manufacturer.substring(_medicine!.manufacturer.length - 6)}',
                            ),
                          ],
                        ),
                      )
                          .animate()
                          .fadeIn(duration: 500.ms, delay: 100.ms),

                      const SizedBox(height: AppSpacing.lg),

                      // Custody chain
                      if (_custodyHistory.isNotEmpty) ...[
                        Text('Custody Chain', style: AppTypography.titleMedium)
                            .animate()
                            .fadeIn(duration: 500.ms, delay: 200.ms),
                        const SizedBox(height: 8),
                        ...List.generate(
                          _custodyHistory.length,
                          (i) {
                            final record = _custodyHistory[i];
                            final isLast = i == _custodyHistory.length - 1;
                            return Row(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                // Timeline
                                SizedBox(
                                  width: 32,
                                  child: Column(
                                    children: [
                                      Container(
                                        width: 12,
                                        height: 12,
                                        decoration: BoxDecoration(
                                          color: isLast ? AppColors.primary : AppColors.border,
                                          shape: BoxShape.circle,
                                          border: isLast
                                              ? Border.all(color: AppColors.primaryLight, width: 3)
                                              : null,
                                        ),
                                      ),
                                      if (!isLast)
                                        Container(
                                          width: 2,
                                          height: 50,
                                          color: AppColors.border,
                                        ),
                                    ],
                                  ),
                                ),
                                Expanded(
                                  child: Container(
                                    margin: const EdgeInsets.only(bottom: 8),
                                    padding: const EdgeInsets.all(12),
                                    decoration: AppDecorations.cardSubtle,
                                    child: Column(
                                      crossAxisAlignment: CrossAxisAlignment.start,
                                      children: [
                                        Row(
                                          children: [
                                            Text(
                                              record.name.isNotEmpty ? record.name : 'Unknown',
                                              style: AppTypography.titleSmall,
                                            ),
                                            const SizedBox(width: 6),
                                            Container(
                                              padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                                              decoration: BoxDecoration(
                                                color: AppColors.primaryLight,
                                                borderRadius: BorderRadius.circular(4),
                                              ),
                                              child: Text(
                                                AppConfig.roleName(record.role),
                                                style: AppTypography.bodySmall.copyWith(
                                                  fontSize: 10,
                                                  color: AppColors.primaryDark,
                                                  fontWeight: FontWeight.w600,
                                                ),
                                              ),
                                            ),
                                          ],
                                        ),
                                        Text(
                                          _dateFormat.format(record.timestamp),
                                          style: AppTypography.bodySmall,
                                        ),
                                        Text(
                                          '${record.address.substring(0, 8)}...${record.address.substring(record.address.length - 6)}',
                                          style: AppTypography.mono.copyWith(fontSize: 10),
                                        ),
                                      ],
                                    ),
                                  ),
                                ),
                              ],
                            )
                                .animate()
                                .fadeIn(
                                  duration: 400.ms,
                                  delay: Duration(milliseconds: 300 + i * 80),
                                )
                                .slideX(begin: 0.05, end: 0, duration: 400.ms);
                          },
                        ),
                      ],

                      const SizedBox(height: AppSpacing.lg),

                      // Scan history
                      if (_scanHistory.isNotEmpty) ...[
                        Text('Scan History (${_scanHistory.length})', style: AppTypography.titleMedium)
                            .animate()
                            .fadeIn(duration: 500.ms, delay: 400.ms),
                        const SizedBox(height: 8),
                        ...List.generate(
                          _scanHistory.length > 10 ? 10 : _scanHistory.length,
                          (i) {
                            final scan = _scanHistory[i];
                            return Container(
                              margin: const EdgeInsets.only(bottom: 8),
                              padding: const EdgeInsets.all(12),
                              decoration: AppDecorations.cardSubtle,
                              child: Row(
                                children: [
                                  Container(
                                    width: 32,
                                    height: 32,
                                    decoration: BoxDecoration(
                                      color: const Color(0xFFE0E7FF),
                                      borderRadius: BorderRadius.circular(8),
                                    ),
                                    child: const Icon(Icons.document_scanner, size: 16, color: Color(0xFF4F46E5)),
                                  ),
                                  const SizedBox(width: 10),
                                  Expanded(
                                    child: Column(
                                      crossAxisAlignment: CrossAxisAlignment.start,
                                      children: [
                                        Text(scan.location, style: AppTypography.bodySmall.copyWith(color: AppColors.textPrimary)),
                                        Text(
                                          '${_dateFormat.format(scan.timestamp)} | ${scan.scanner.substring(0, 8)}...',
                                          style: AppTypography.bodySmall.copyWith(fontSize: 10),
                                        ),
                                      ],
                                    ),
                                  ),
                                ],
                              ),
                            )
                                .animate()
                                .fadeIn(
                                  duration: 400.ms,
                                  delay: Duration(milliseconds: 500 + i * 60),
                                );
                          },
                        ),
                      ],

                      const SizedBox(height: AppSpacing.xxl),
                    ],
                  ),
                ),
    );
  }
}

class _Row extends StatelessWidget {
  final String label;
  final String value;

  const _Row({required this.label, required this.value});

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
