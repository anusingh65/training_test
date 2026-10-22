import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';
import '../../config/app_config.dart';
import '../../models/custody_record_model.dart';
import '../../models/scan_record_model.dart';
import '../../services/blockchain_service.dart';
import '../../services/scanner_service.dart';
import '../../services/cache_service.dart';
import '../../theme/app_theme.dart';

class HistoryScreen extends StatefulWidget {
  final int? medicineId;

  const HistoryScreen({super.key, this.medicineId});

  @override
  State<HistoryScreen> createState() => _HistoryScreenState();
}

class _HistoryScreenState extends State<HistoryScreen> with SingleTickerProviderStateMixin {
  late TabController _tabController;
  final _searchController = TextEditingController();
  List<CustodyRecordModel> _custodyHistory = [];
  List<ScanRecordModel> _scanHistory = [];
  bool _isLoading = false;
  int? _currentMedicineId;
  final _dateFormat = DateFormat('dd MMM yyyy, HH:mm');

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
    if (widget.medicineId != null) {
      _currentMedicineId = widget.medicineId;
      _searchController.text = widget.medicineId.toString();
      _loadHistory(widget.medicineId!);
    }
  }

  @override
  void dispose() {
    _tabController.dispose();
    _searchController.dispose();
    super.dispose();
  }

  Future<void> _loadHistory(int medicineId) async {
    setState(() {
      _isLoading = true;
      _currentMedicineId = medicineId;
    });

    try {
      final blockchainService = context.read<BlockchainService>();
      final scannerService = context.read<ScannerService>();
      final cacheService = context.read<CacheService>();

      // Load custody history
      final custody = await blockchainService.getCustodyHistory(medicineId);

      // Resolve actor names
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
      final scans = await scannerService.getScanHistory(medicineId);

      if (mounted) {
        setState(() {
          _custodyHistory = resolvedCustody;
          _scanHistory = scans;
          _isLoading = false;
        });
      }
    } catch (e) {
      if (mounted) setState(() => _isLoading = false);
      debugPrint('Load history error: $e');
    }
  }

  void _searchMedicine() {
    final id = int.tryParse(_searchController.text.trim());
    if (id != null && id > 0) {
      _loadHistory(id);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        title: const Text('Transaction History'),
        bottom: TabBar(
          controller: _tabController,
          labelColor: AppColors.primary,
          unselectedLabelColor: AppColors.textTertiary,
          indicatorColor: AppColors.primary,
          tabs: const [
            Tab(text: 'Custody Chain'),
            Tab(text: 'Scan Audit'),
          ],
        ),
      ),
      body: Column(
        children: [
          // Search bar
          Container(
            padding: const EdgeInsets.all(AppSpacing.md),
            color: AppColors.surface,
            child: Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _searchController,
                    decoration: InputDecoration(
                      hintText: 'Enter Medicine ID',
                      prefixIcon: const Icon(Icons.search, size: 20),
                      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
                      border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                    ),
                    keyboardType: TextInputType.number,
                    onSubmitted: (_) => _searchMedicine(),
                  ),
                ),
                const SizedBox(width: 8),
                SizedBox(
                  height: 48,
                  child: ElevatedButton(
                    onPressed: _isLoading ? null : _searchMedicine,
                    style: ElevatedButton.styleFrom(backgroundColor: AppColors.primary),
                    child: const Text('Search'),
                  ),
                ),
              ],
            ),
          )
              .animate()
              .fadeIn(duration: 400.ms),

          // Tabs content
          Expanded(
            child: _isLoading
                ? const Center(child: CircularProgressIndicator(color: AppColors.primary))
                : _currentMedicineId == null
                    ? Center(
                        child: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Icon(Icons.search, size: 64, color: AppColors.textTertiary.withValues(alpha: 0.5)),
                            const SizedBox(height: 16),
                            Text('Enter a Medicine ID to view history', style: AppTypography.bodyMedium),
                          ],
                        ),
                      )
                    : TabBarView(
                        controller: _tabController,
                        children: [
                          _buildCustodyTab(),
                          _buildScanTab(),
                        ],
                      ),
          ),
        ],
      ),
    );
  }

  Widget _buildCustodyTab() {
    if (_custodyHistory.isEmpty) {
      return const Center(child: Text('No custody history found'));
    }

    return ListView.builder(
      padding: const EdgeInsets.all(AppSpacing.md),
      itemCount: _custodyHistory.length,
      itemBuilder: (context, i) {
        final record = _custodyHistory[i];
        final isFirst = i == 0;
        final isLast = i == _custodyHistory.length - 1;

        return Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Timeline
            SizedBox(
              width: 40,
              child: Column(
                children: [
                  if (!isFirst)
                    Container(width: 2, height: 8, color: AppColors.primary.withValues(alpha: 0.3)),
                  Container(
                    width: 16,
                    height: 16,
                    decoration: BoxDecoration(
                      color: isLast ? AppColors.primary : AppColors.primaryLight,
                      shape: BoxShape.circle,
                      border: Border.all(color: AppColors.primary, width: 2),
                    ),
                    child: isLast
                        ? const Icon(Icons.check, size: 10, color: Colors.white)
                        : null,
                  ),
                  if (!isLast)
                    Container(width: 2, height: 60, color: AppColors.primary.withValues(alpha: 0.3)),
                ],
              ),
            ),
            Expanded(
              child: Container(
                margin: const EdgeInsets.only(bottom: 8),
                padding: const EdgeInsets.all(14),
                decoration: AppDecorations.card,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Expanded(
                          child: Text(
                            record.name.isNotEmpty ? record.name : 'Unknown Actor',
                            style: AppTypography.titleSmall,
                          ),
                        ),
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                          decoration: BoxDecoration(
                            color: _roleColor(record.role).withValues(alpha: 0.1),
                            borderRadius: BorderRadius.circular(6),
                          ),
                          child: Text(
                            AppConfig.roleName(record.role),
                            style: TextStyle(
                              fontSize: 10,
                              fontWeight: FontWeight.w600,
                              color: _roleColor(record.role),
                            ),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 4),
                    if (record.location.isNotEmpty)
                      Row(
                        children: [
                          const Icon(Icons.location_on, size: 12, color: AppColors.textTertiary),
                          const SizedBox(width: 4),
                          Text(record.location, style: AppTypography.bodySmall),
                        ],
                      ),
                    const SizedBox(height: 2),
                    Row(
                      children: [
                        const Icon(Icons.access_time, size: 12, color: AppColors.textTertiary),
                        const SizedBox(width: 4),
                        Text(_dateFormat.format(record.timestamp), style: AppTypography.bodySmall),
                      ],
                    ),
                    const SizedBox(height: 2),
                    Text(
                      record.address,
                      style: AppTypography.mono.copyWith(fontSize: 10),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ],
                ),
              ),
            ),
          ],
        )
            .animate()
            .fadeIn(duration: 400.ms, delay: Duration(milliseconds: i * 80))
            .slideX(begin: 0.05, end: 0, duration: 400.ms);
      },
    );
  }

  Widget _buildScanTab() {
    if (_scanHistory.isEmpty) {
      return const Center(child: Text('No scan records found'));
    }

    return ListView.builder(
      padding: const EdgeInsets.all(AppSpacing.md),
      itemCount: _scanHistory.length,
      itemBuilder: (context, i) {
        final scan = _scanHistory[i];
        return Container(
          margin: const EdgeInsets.only(bottom: 8),
          padding: const EdgeInsets.all(14),
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
                child: Center(
                  child: Text(
                    '${i + 1}',
                    style: AppTypography.titleSmall.copyWith(color: const Color(0xFF4F46E5)),
                  ),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(scan.location, style: AppTypography.titleSmall),
                    const SizedBox(height: 2),
                    Text(
                      _dateFormat.format(scan.timestamp),
                      style: AppTypography.bodySmall,
                    ),
                    Row(
                      children: [
                        const Icon(Icons.gps_fixed, size: 11, color: AppColors.textTertiary),
                        const SizedBox(width: 3),
                        Text(
                          '${scan.latitude.toStringAsFixed(4)}, ${scan.longitude.toStringAsFixed(4)}',
                          style: AppTypography.mono.copyWith(fontSize: 10),
                        ),
                      ],
                    ),
                    Text(
                      'Scanner: ${scan.scanner.substring(0, 10)}...',
                      style: AppTypography.mono.copyWith(fontSize: 10),
                    ),
                  ],
                ),
              ),
            ],
          ),
        )
            .animate()
            .fadeIn(duration: 400.ms, delay: Duration(milliseconds: i * 60))
            .slideX(begin: 0.05, end: 0, duration: 400.ms);
      },
    );
  }

  Color _roleColor(int role) {
    switch (role) {
      case 1: return const Color(0xFF7C3AED); // Manufacturer
      case 2: return AppColors.primary; // Distributor
      case 3: return const Color(0xFF3B82F6); // Pharmacy
      case 6: return const Color(0xFFF59E0B); // Admin
      default: return AppColors.textSecondary;
    }
  }
}
