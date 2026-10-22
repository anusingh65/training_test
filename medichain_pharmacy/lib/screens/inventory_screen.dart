import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:provider/provider.dart';
import '../services/inventory_service.dart';
import '../models/medicine_item.dart';
import '../theme/app_theme.dart';
import 'medicine_detail_screen.dart';

class InventoryScreen extends StatefulWidget {
  const InventoryScreen({super.key});

  @override
  State<InventoryScreen> createState() => _InventoryScreenState();
}

class _InventoryScreenState extends State<InventoryScreen>
    with SingleTickerProviderStateMixin {
  late TabController _tabCtrl;

  @override
  void initState() {
    super.initState();
    _tabCtrl = TabController(length: 3, vsync: this);
  }

  @override
  void dispose() {
    _tabCtrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final inv = context.watch<InventoryService>();

    return SafeArea(
      child: Column(
        children: [
          // Header
          Padding(
            padding: const EdgeInsets.fromLTRB(
                AppSpacing.lg, AppSpacing.lg, AppSpacing.lg, 0),
            child: Row(
              children: [
                Text('Inventory', style: AppTypography.displayMedium),
                const Spacer(),
                Container(
                  padding: const EdgeInsets.symmetric(
                      horizontal: 12, vertical: 6),
                  decoration: BoxDecoration(
                    color: AppColors.primary.withValues(alpha: 0.1),
                    borderRadius: BorderRadius.circular(20),
                  ),
                  child: Text(
                    '${inv.totalItems} items',
                    style: AppTypography.labelLarge
                        .copyWith(color: AppColors.primary),
                  ),
                ),
              ],
            ),
          ),

          // Tabs
          TabBar(
            controller: _tabCtrl,
            labelColor: AppColors.primary,
            unselectedLabelColor: AppColors.textTertiary,
            indicatorColor: AppColors.primary,
            tabs: [
              Tab(text: 'All (${inv.totalItems})'),
              Tab(text: 'In Stock (${inv.availableCount})'),
              Tab(text: 'Sold (${inv.dispensedCount})'),
            ],
          ),

          // Tab views
          Expanded(
            child: TabBarView(
              controller: _tabCtrl,
              children: [
                _MedicineList(items: inv.inventory),
                _MedicineList(items: inv.availableInventory),
                _MedicineList(items: inv.dispensedInventory),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _MedicineList extends StatelessWidget {
  final List<MedicineItem> items;

  const _MedicineList({required this.items});

  @override
  Widget build(BuildContext context) {
    if (items.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.inventory_2_outlined,
                size: 64, color: AppColors.textTertiary),
            const SizedBox(height: AppSpacing.md),
            Text('No items', style: AppTypography.bodyMedium),
          ],
        ),
      );
    }

    return ListView.builder(
      padding: const EdgeInsets.all(AppSpacing.md),
      itemCount: items.length,
      itemBuilder: (context, index) {
        final med = items[index];
        final statusColor = med.isAtPharmacy
            ? AppColors.success
            : med.isDispensed
                ? AppColors.info
                : med.isFlagged
                    ? AppColors.error
                    : AppColors.warning;

        return Container(
          margin: const EdgeInsets.only(bottom: AppSpacing.sm),
          child: Material(
            color: Colors.transparent,
            child: InkWell(
              borderRadius: BorderRadius.circular(16),
              onTap: () => Navigator.push(
                context,
                MaterialPageRoute(
                  builder: (_) => MedicineDetailScreen(medicine: med),
                ),
              ),
              child: Container(
                padding: const EdgeInsets.all(AppSpacing.md),
                decoration: AppDecorations.card,
                child: Row(
                  children: [
                    Container(
                      width: 48,
                      height: 48,
                      decoration: BoxDecoration(
                        color: statusColor.withValues(alpha: 0.1),
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: Icon(Icons.medication_outlined,
                          color: statusColor, size: 24),
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
                        color: statusColor.withValues(alpha: 0.1),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Text(
                        med.statusLabel,
                        style: AppTypography.bodySmall
                            .copyWith(color: statusColor, fontSize: 11),
                      ),
                    ),
                    const SizedBox(width: AppSpacing.sm),
                    const Icon(Icons.chevron_right,
                        color: AppColors.textTertiary, size: 20),
                  ],
                ),
              ),
            ),
          ),
        )
            .animate()
            .fadeIn(
                duration: 300.ms,
                delay: Duration(milliseconds: 50 * index.clamp(0, 10)))
            .slideX(
                begin: 0.05,
                end: 0,
                duration: 300.ms,
                delay: Duration(milliseconds: 50 * index.clamp(0, 10)));
      },
    );
  }
}
