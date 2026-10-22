import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';
import '../models/medicine_item.dart';
import '../services/blockchain_service.dart';
import '../theme/app_theme.dart';

class MedicineDetailScreen extends StatefulWidget {
  final MedicineItem medicine;

  const MedicineDetailScreen({super.key, required this.medicine});

  @override
  State<MedicineDetailScreen> createState() => _MedicineDetailScreenState();
}

class _MedicineDetailScreenState extends State<MedicineDetailScreen> {
  List<String>? _custodyAddresses;
  List<DateTime>? _custodyTimestamps;
  bool _loadingHistory = true;

  @override
  void initState() {
    super.initState();
    _loadCustodyHistory();
  }

  Future<void> _loadCustodyHistory() async {
    final blockchain = context.read<BlockchainService>();
    final history = await blockchain.getCustodyHistory(widget.medicine.id);
    if (mounted) {
      setState(() {
        _custodyAddresses = history.addresses;
        _custodyTimestamps = history.timestamps;
        _loadingHistory = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final med = widget.medicine;
    final statusColor = med.isAtPharmacy
        ? AppColors.success
        : med.isDispensed
            ? AppColors.info
            : med.isFlagged
                ? AppColors.error
                : AppColors.warning;

    return Scaffold(
      appBar: AppBar(title: Text('Medicine #${med.id}'), centerTitle: true),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(AppSpacing.lg),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Status header
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(AppSpacing.lg),
              decoration: AppDecorations.gradientCard(
                med.isAtPharmacy
                    ? [const Color(0xFF6366F1), const Color(0xFF4F46E5)]
                    : med.isDispensed
                        ? [const Color(0xFF10B981), const Color(0xFF059669)]
                        : [const Color(0xFFF59E0B), const Color(0xFFD97706)],
              ),
              child: Column(
                children: [
                  Icon(
                    med.isAtPharmacy
                        ? Icons.inventory_2_outlined
                        : med.isDispensed
                            ? Icons.check_circle_outline
                            : Icons.warning_outlined,
                    size: 48,
                    color: Colors.white,
                  ),
                  const SizedBox(height: AppSpacing.sm),
                  Text(
                    med.statusLabel,
                    style: AppTypography.titleLarge
                        .copyWith(color: Colors.white),
                  ),
                ],
              ),
            )
                .animate()
                .fadeIn(duration: 500.ms)
                .scaleXY(begin: 0.95, end: 1, duration: 500.ms),

            const SizedBox(height: AppSpacing.lg),

            // Details card
            Container(
              padding: const EdgeInsets.all(AppSpacing.lg),
              decoration: AppDecorations.elevatedCard,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('Details', style: AppTypography.titleLarge),
                  const SizedBox(height: AppSpacing.md),
                  _DetailRow(label: 'Medicine ID', value: '#${med.id}'),
                  _DetailRow(
                      label: 'Batch',
                      value: '${med.batchNumber ?? med.batchId}'),
                  _DetailRow(label: 'Status', value: med.statusLabel,
                      valueColor: statusColor),
                  _DetailRow(
                    label: 'Owner',
                    value: _shortAddr(med.currentOwner),
                    trailing: IconButton(
                      icon: const Icon(Icons.copy, size: 16),
                      onPressed: () {
                        Clipboard.setData(
                            ClipboardData(text: med.currentOwner));
                        ScaffoldMessenger.of(context).showSnackBar(
                          const SnackBar(content: Text('Address copied')),
                        );
                      },
                    ),
                  ),
                  if (med.ipfsHash.isNotEmpty)
                    _DetailRow(
                        label: 'IPFS',
                        value: _shortAddr(med.ipfsHash)),
                ],
              ),
            ).animate().fadeIn(duration: 500.ms, delay: 200.ms),

            const SizedBox(height: AppSpacing.lg),

            // Custody History
            Container(
              padding: const EdgeInsets.all(AppSpacing.lg),
              decoration: AppDecorations.elevatedCard,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('Custody History', style: AppTypography.titleLarge),
                  const SizedBox(height: AppSpacing.md),
                  if (_loadingHistory)
                    const Center(child: CircularProgressIndicator())
                  else if (_custodyAddresses == null ||
                      _custodyAddresses!.isEmpty)
                    Text('No history available',
                        style: AppTypography.bodyMedium)
                  else
                    ...List.generate(_custodyAddresses!.length, (i) {
                      final addr = _custodyAddresses![i];
                      final time = _custodyTimestamps != null &&
                              i < _custodyTimestamps!.length
                          ? DateFormat('MMM d, y HH:mm')
                              .format(_custodyTimestamps![i])
                          : '';

                      return Padding(
                        padding:
                            const EdgeInsets.only(bottom: AppSpacing.md),
                        child: Row(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Column(
                              children: [
                                Container(
                                  width: 12,
                                  height: 12,
                                  decoration: BoxDecoration(
                                    color: i == _custodyAddresses!.length - 1
                                        ? AppColors.primary
                                        : AppColors.textTertiary,
                                    shape: BoxShape.circle,
                                  ),
                                ),
                                if (i < _custodyAddresses!.length - 1)
                                  Container(
                                    width: 2,
                                    height: 36,
                                    color: AppColors.border,
                                  ),
                              ],
                            ),
                            const SizedBox(width: AppSpacing.md),
                            Expanded(
                              child: Column(
                                crossAxisAlignment:
                                    CrossAxisAlignment.start,
                                children: [
                                  Text(_shortAddr(addr),
                                      style: AppTypography.mono),
                                  if (time.isNotEmpty)
                                    Text(time,
                                        style: AppTypography.bodySmall),
                                ],
                              ),
                            ),
                          ],
                        ),
                      );
                    }),
                ],
              ),
            ).animate().fadeIn(duration: 500.ms, delay: 400.ms),
          ],
        ),
      ),
    );
  }

  String _shortAddr(String addr) {
    if (addr.length > 14) {
      return '${addr.substring(0, 8)}...${addr.substring(addr.length - 6)}';
    }
    return addr;
  }
}

class _DetailRow extends StatelessWidget {
  final String label;
  final String value;
  final Color? valueColor;
  final Widget? trailing;

  const _DetailRow({
    required this.label,
    required this.value,
    this.valueColor,
    this.trailing,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: AppSpacing.md),
      child: Row(
        children: [
          Expanded(
            flex: 2,
            child: Text(label, style: AppTypography.bodyMedium),
          ),
          Expanded(
            flex: 3,
            child: Row(
              mainAxisAlignment: MainAxisAlignment.end,
              children: [
                Flexible(
                  child: Text(
                    value,
                    style: AppTypography.titleSmall.copyWith(
                        color: valueColor ?? AppColors.textPrimary),
                    textAlign: TextAlign.end,
                  ),
                ),
                if (trailing != null) trailing!,
              ],
            ),
          ),
        ],
      ),
    );
  }
}
