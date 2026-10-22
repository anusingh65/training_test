import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';
import 'dart:math' as math;
import '../../models/batch_model.dart';
import '../../models/medicine_model.dart';
import '../../services/blockchain_service.dart';
import '../../theme/app_theme.dart';
import '../../widgets/page_route.dart';
import 'register_strips_screen.dart';
import 'qr_viewer_screen.dart';

class BatchDetailScreen extends StatefulWidget {
  final BatchModel batch;

  const BatchDetailScreen({super.key, required this.batch});

  @override
  State<BatchDetailScreen> createState() => _BatchDetailScreenState();
}

class _BatchDetailScreenState extends State<BatchDetailScreen>
    with SingleTickerProviderStateMixin {
  bool _isLoadingQR = false;
  late AnimationController _progressController;
  late Animation<double> _progressAnimation;

  @override
  void initState() {
    super.initState();
    _progressController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1200),
    );
    _progressAnimation = Tween<double>(
      begin: 0,
      end: widget.batch.completionPercentage / 100,
    ).animate(CurvedAnimation(
      parent: _progressController,
      curve: Curves.easeOutCubic,
    ));
    Future.delayed(const Duration(milliseconds: 400), () {
      if (mounted) _progressController.forward();
    });
  }

  @override
  void dispose() {
    _progressController.dispose();
    super.dispose();
  }

  Future<void> _openQRViewer() async {
    setState(() => _isLoadingQR = true);
    try {
      final blockchainService = context.read<BlockchainService>();

      final medicineIds = await blockchainService.getBatchMedicines(
        widget.batch.batchId,
      );

      final medicines = medicineIds.map((id) {
        return MedicineModel(
          medicineId: id,
          batchId: widget.batch.batchId,
          medicineName: widget.batch.medicineName,
          composition: widget.batch.composition,
          dosage: widget.batch.dosage,
          batchNumber: widget.batch.batchNumber,
          manufactureDate: widget.batch.manufactureDate,
          expiryDate: widget.batch.expiryDate,
        );
      }).toList();

      if (mounted) {
        Navigator.push(
          context,
          FadeSlideRoute(
            page: QRViewerScreen(
              batch: widget.batch,
              medicines: medicines,
            ),
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Failed to load QR codes: $e'),
            backgroundColor: AppColors.error,
          ),
        );
      }
    } finally {
      if (mounted) setState(() => _isLoadingQR = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final batch = widget.batch;
    final dateFormat = DateFormat('MMM dd, yyyy');

    return Scaffold(
      appBar: AppBar(
        title: Text('Batch ${batch.batchNumber}', style: AppTypography.titleLarge),
      ),
      body: ListView(
        padding: const EdgeInsets.all(AppSpacing.md),
        children: [
          // Status Card with Hero
          Hero(
            tag: 'batch-${batch.batchId}',
            child: Material(
              color: Colors.transparent,
              child: Container(
                padding: const EdgeInsets.all(AppSpacing.lg),
                decoration: BoxDecoration(
                  color: AppColors.surface,
                  borderRadius: BorderRadius.circular(20),
                  boxShadow: const [
                    BoxShadow(
                      color: AppColors.shadowLight,
                      blurRadius: 10,
                      offset: Offset(0, 2),
                    ),
                    BoxShadow(
                      color: AppColors.shadowMedium,
                      blurRadius: 30,
                      offset: Offset(0, 10),
                    ),
                  ],
                ),
                child: Column(
                  children: [
                    Text(
                      batch.medicineName,
                      style: AppTypography.displayMedium,
                      textAlign: TextAlign.center,
                    ),
                    const SizedBox(height: AppSpacing.xs),
                    Text(
                      'Batch #${batch.batchNumber}',
                      style: AppTypography.bodyMedium,
                    ),
                    const SizedBox(height: AppSpacing.lg),

                    // Circular + linear progress
                    Row(
                      children: [
                        SizedBox(
                          width: 64,
                          height: 64,
                          child: AnimatedBuilder(
                            animation: _progressAnimation,
                            builder: (context, child) {
                              return CustomPaint(
                                painter: _GradientProgressPainter(
                                  progress: _progressAnimation.value,
                                  strokeWidth: 5,
                                ),
                                child: Center(
                                  child: TweenAnimationBuilder<int>(
                                    tween: IntTween(
                                      begin: 0,
                                      end: batch.completionPercentage.toInt(),
                                    ),
                                    duration: const Duration(milliseconds: 1200),
                                    curve: Curves.easeOutCubic,
                                    builder: (context, val, _) {
                                      return Text(
                                        '$val%',
                                        style: AppTypography.labelLarge,
                                      );
                                    },
                                  ),
                                ),
                              );
                            },
                          ),
                        ),
                        const SizedBox(width: AppSpacing.md),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                '${batch.registeredUnits} / ${batch.totalUnits} strips registered',
                                style: AppTypography.titleSmall,
                              ),
                              const SizedBox(height: AppSpacing.sm),
                              ClipRRect(
                                borderRadius: BorderRadius.circular(4),
                                child: AnimatedBuilder(
                                  animation: _progressAnimation,
                                  builder: (context, _) {
                                    return LinearProgressIndicator(
                                      value: _progressAnimation.value,
                                      minHeight: 8,
                                      backgroundColor: AppColors.border,
                                      color: AppColors.primary,
                                    );
                                  },
                                ),
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ),
          ),

          const SizedBox(height: AppSpacing.md),

          // Medicine Details
          Container(
            padding: const EdgeInsets.all(AppSpacing.md),
            decoration: AppDecorations.elevatedCard,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('Medicine Details', style: AppTypography.titleMedium),
                const Divider(height: 24),
                _buildDetailRow('Composition', batch.composition, 0),
                _buildDetailRow('Dosage', batch.dosage, 1),
                _buildDetailRow('Manufacture Date', dateFormat.format(batch.manufactureDate), 2),
                _buildDetailRow('Expiry Date', dateFormat.format(batch.expiryDate), 3),
              ],
            ),
          )
              .animate()
              .fadeIn(duration: 500.ms, delay: 300.ms)
              .slideY(begin: 0.15, end: 0, duration: 500.ms, delay: 300.ms, curve: Curves.easeOutCubic),

          const SizedBox(height: AppSpacing.md),

          // Manufacturer Details
          Container(
            padding: const EdgeInsets.all(AppSpacing.md),
            decoration: AppDecorations.elevatedCard,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('Manufacturer Details', style: AppTypography.titleMedium),
                const Divider(height: 24),
                _buildDetailRow('Name', batch.manufacturerName, 0),
                _buildDetailRow('License', batch.manufacturerLicense, 1),
                _buildDetailRow('Location', batch.manufacturerLocation, 2),
              ],
            ),
          )
              .animate()
              .fadeIn(duration: 500.ms, delay: 450.ms)
              .slideY(begin: 0.15, end: 0, duration: 500.ms, delay: 450.ms, curve: Curves.easeOutCubic),

          const SizedBox(height: AppSpacing.lg),

          // Action Buttons
          if (!batch.isComplete)
            Container(
              decoration: BoxDecoration(
                gradient: AppGradients.primary,
                borderRadius: BorderRadius.circular(12),
                boxShadow: [
                  BoxShadow(
                    color: AppColors.primary.withValues(alpha: 0.3),
                    blurRadius: 12,
                    offset: const Offset(0, 4),
                  ),
                ],
              ),
              child: SizedBox(
                width: double.infinity,
                child: ElevatedButton.icon(
                  onPressed: () {
                    HapticFeedback.lightImpact();
                    Navigator.push(
                      context,
                      FadeSlideRoute(
                        page: RegisterStripsScreen(batch: batch),
                      ),
                    );
                  },
                  icon: const Icon(Icons.app_registration),
                  label: const Text('Register Strips'),
                  style: ElevatedButton.styleFrom(
                    padding: const EdgeInsets.symmetric(vertical: 14),
                    backgroundColor: Colors.transparent,
                    shadowColor: Colors.transparent,
                  ),
                ),
              ),
            )
                .animate()
                .fadeIn(duration: 500.ms, delay: 600.ms)
                .slideY(begin: 0.2, end: 0, duration: 500.ms, delay: 600.ms),

          if (!batch.isComplete) const SizedBox(height: AppSpacing.sm),

          if (batch.registeredUnits > 0)
            SizedBox(
              width: double.infinity,
              child: OutlinedButton.icon(
                onPressed: _isLoadingQR ? null : _openQRViewer,
                icon: _isLoadingQR
                    ? const SizedBox(
                        width: 18,
                        height: 18,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : const Icon(Icons.qr_code),
                label: Text(_isLoadingQR ? 'Loading...' : 'View QR Codes'),
                style: OutlinedButton.styleFrom(
                  padding: const EdgeInsets.symmetric(vertical: 14),
                ),
              ),
            )
                .animate()
                .fadeIn(duration: 500.ms, delay: 700.ms),

          if (batch.registeredUnits > 0) const SizedBox(height: AppSpacing.sm),

          if (batch.isComplete)
            Container(
              padding: const EdgeInsets.all(AppSpacing.md),
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  colors: [
                    AppColors.success.withValues(alpha: 0.1),
                    AppColors.success.withValues(alpha: 0.05),
                  ],
                ),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: AppColors.success.withValues(alpha: 0.3)),
              ),
              child: Row(
                children: [
                  const Icon(Icons.check_circle, color: AppColors.success, size: 22),
                  const SizedBox(width: AppSpacing.sm),
                  Expanded(
                    child: Text(
                      'Batch is complete and ready for distribution',
                      style: AppTypography.titleSmall.copyWith(color: AppColors.success),
                    ),
                  ),
                ],
              ),
            )
                .animate()
                .fadeIn(duration: 500.ms, delay: 600.ms)
                .slideY(begin: -0.2, end: 0, duration: 500.ms, delay: 600.ms, curve: Curves.easeOutBack),

          const SizedBox(height: AppSpacing.md),
        ],
      ),
    );
  }

  Widget _buildDetailRow(String label, String value, int index) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 120,
            child: Text(label, style: AppTypography.bodyMedium),
          ),
          Expanded(
            child: Text(
              value,
              style: AppTypography.bodyLarge.copyWith(fontWeight: FontWeight.w500),
            ),
          ),
        ],
      ),
    );
  }
}

// Custom gradient progress ring painter
class _GradientProgressPainter extends CustomPainter {
  final double progress;
  final double strokeWidth;

  _GradientProgressPainter({
    required this.progress,
    required this.strokeWidth,
  });

  @override
  void paint(Canvas canvas, Size size) {
    final center = Offset(size.width / 2, size.height / 2);
    final radius = (size.width - strokeWidth) / 2;

    // Background track
    final trackPaint = Paint()
      ..color = AppColors.border
      ..style = PaintingStyle.stroke
      ..strokeWidth = strokeWidth
      ..strokeCap = StrokeCap.round;
    canvas.drawCircle(center, radius, trackPaint);

    if (progress <= 0) return;

    // Gradient arc
    final rect = Rect.fromCircle(center: center, radius: radius);
    final gradient = SweepGradient(
      startAngle: -math.pi / 2,
      endAngle: 3 * math.pi / 2,
      colors: const [
        Color(0xFF10B981),
        Color(0xFF059669),
      ],
    );

    final progressPaint = Paint()
      ..shader = gradient.createShader(rect)
      ..style = PaintingStyle.stroke
      ..strokeWidth = strokeWidth
      ..strokeCap = StrokeCap.round;

    canvas.drawArc(
      rect,
      -math.pi / 2,
      2 * math.pi * progress,
      false,
      progressPaint,
    );
  }

  @override
  bool shouldRepaint(_GradientProgressPainter oldDelegate) {
    return oldDelegate.progress != progress;
  }
}
