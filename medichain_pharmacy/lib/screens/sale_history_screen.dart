import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';
import '../services/inventory_service.dart';
import '../theme/app_theme.dart';

class SaleHistoryScreen extends StatelessWidget {
  const SaleHistoryScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final inv = context.watch<InventoryService>();
    final sales = inv.sales;

    return SafeArea(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(
                AppSpacing.lg, AppSpacing.lg, AppSpacing.lg, 0),
            child: Row(
              children: [
                Text('Sales History', style: AppTypography.displayMedium),
                const Spacer(),
                Container(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                  decoration: BoxDecoration(
                    color: AppColors.success.withValues(alpha: 0.1),
                    borderRadius: BorderRadius.circular(20),
                  ),
                  child: Text(
                    '${sales.length} sales',
                    style: AppTypography.labelLarge
                        .copyWith(color: AppColors.success),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: AppSpacing.md),
          Expanded(
            child: sales.isEmpty
                ? Center(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Icon(Icons.receipt_long_outlined,
                            size: 64, color: AppColors.textTertiary),
                        const SizedBox(height: AppSpacing.md),
                        Text('No sales recorded',
                            style: AppTypography.bodyMedium),
                        const SizedBox(height: AppSpacing.xs),
                        Text(
                          'Completed sales will appear here',
                          style: AppTypography.bodySmall,
                        ),
                      ],
                    ),
                  )
                : ListView.builder(
                    padding: const EdgeInsets.symmetric(
                        horizontal: AppSpacing.lg),
                    itemCount: sales.length,
                    itemBuilder: (context, index) {
                      final sale = sales[index];
                      final dateStr =
                          DateFormat('MMM d, y  HH:mm').format(sale.timestamp);

                      return Container(
                        margin: const EdgeInsets.only(bottom: AppSpacing.md),
                        padding: const EdgeInsets.all(AppSpacing.md),
                        decoration: AppDecorations.card,
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(
                              children: [
                                Container(
                                  width: 40,
                                  height: 40,
                                  decoration: BoxDecoration(
                                    color: AppColors.success
                                        .withValues(alpha: 0.1),
                                    borderRadius: BorderRadius.circular(10),
                                  ),
                                  child: const Icon(
                                      Icons.check_circle_outline,
                                      color: AppColors.success,
                                      size: 20),
                                ),
                                const SizedBox(width: AppSpacing.md),
                                Expanded(
                                  child: Column(
                                    crossAxisAlignment:
                                        CrossAxisAlignment.start,
                                    children: [
                                      Text(
                                        'Medicine #${sale.medicineId}',
                                        style: AppTypography.titleSmall,
                                      ),
                                      Text(
                                        'Batch: ${sale.batchNumber ?? sale.batchId}',
                                        style: AppTypography.bodySmall,
                                      ),
                                    ],
                                  ),
                                ),
                                Text(dateStr, style: AppTypography.bodySmall),
                              ],
                            ),
                            const Divider(height: 20),
                            Row(
                              children: [
                                const Icon(Icons.person_outline,
                                    size: 16, color: AppColors.textTertiary),
                                const SizedBox(width: 6),
                                Text(
                                  sale.customerName != null
                                      ? '${sale.customerName} (${sale.shortCustomer})'
                                      : sale.shortCustomer,
                                  style: AppTypography.mono,
                                ),
                              ],
                            ),
                            const SizedBox(height: AppSpacing.xs),
                            Row(
                              children: [
                                const Icon(Icons.tag,
                                    size: 16, color: AppColors.textTertiary),
                                const SizedBox(width: 6),
                                Text('Tx: ${sale.shortTx}',
                                    style: AppTypography.mono),
                                const SizedBox(width: 4),
                                InkWell(
                                  onTap: () {
                                    Clipboard.setData(
                                        ClipboardData(text: sale.txHash));
                                    ScaffoldMessenger.of(context).showSnackBar(
                                      const SnackBar(
                                          content: Text('Tx hash copied')),
                                    );
                                  },
                                  child: const Icon(Icons.copy,
                                      size: 14, color: AppColors.textTertiary),
                                ),
                              ],
                            ),
                          ],
                        ),
                      )
                          .animate()
                          .fadeIn(
                              duration: 300.ms,
                              delay: Duration(
                                  milliseconds: 50 * index.clamp(0, 10)))
                          .slideY(
                              begin: 0.05,
                              end: 0,
                              duration: 300.ms,
                              delay: Duration(
                                  milliseconds: 50 * index.clamp(0, 10)));
                    },
                  ),
          ),
        ],
      ),
    );
  }
}
