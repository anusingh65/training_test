import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:provider/provider.dart';
import '../../models/batch_model.dart';
import '../../models/medicine_model.dart';
import '../../services/qr_service.dart';
import '../../theme/app_theme.dart';

class QRViewerScreen extends StatefulWidget {
  final BatchModel batch;
  final List<MedicineModel> medicines;

  const QRViewerScreen({
    super.key,
    required this.batch,
    required this.medicines,
  });

  @override
  State<QRViewerScreen> createState() => _QRViewerScreenState();
}

class _QRViewerScreenState extends State<QRViewerScreen> {
  bool _isPrinting = false;

  @override
  Widget build(BuildContext context) {
    final qrService = context.read<QRService>();
    final batchQRData = qrService.generateBatchQRData(
      batchId: widget.batch.batchId,
      batchNumber: widget.batch.batchNumber,
      totalUnits: widget.batch.totalUnits,
    );

    return Scaffold(
      appBar: AppBar(
        title: Text('QR Codes', style: AppTypography.titleLarge),
        actions: [
          IconButton(
            icon: const Icon(Icons.share),
            onPressed: _isPrinting ? null : () => _sharePDF(qrService, batchQRData),
          ),
          IconButton(
            icon: const Icon(Icons.print),
            onPressed: _isPrinting ? null : () => _printPDF(qrService, batchQRData),
          ),
        ],
      ),
      body: ListView(
        padding: const EdgeInsets.all(AppSpacing.md),
        children: [
          // Batch QR Card
          Container(
            padding: const EdgeInsets.all(AppSpacing.lg),
            decoration: AppDecorations.elevatedCard,
            child: Column(
              children: [
                Text('Batch QR Code', style: AppTypography.titleMedium),
                const SizedBox(height: AppSpacing.xs),
                Text(
                  widget.batch.batchNumber,
                  style: AppTypography.bodyMedium,
                ),
                const SizedBox(height: AppSpacing.md),
                Center(
                  child: qrService.generateQRWidget(
                    data: batchQRData,
                    size: 220,
                  ),
                )
                    .animate()
                    .scaleXY(begin: 0.5, end: 1.0, duration: 600.ms, delay: 200.ms, curve: Curves.easeOutBack)
                    .fadeIn(duration: 400.ms, delay: 200.ms),
                const SizedBox(height: AppSpacing.md),
                Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 16,
                    vertical: 8,
                  ),
                  decoration: BoxDecoration(
                    gradient: AppGradients.primary,
                    borderRadius: BorderRadius.circular(20),
                  ),
                  child: Text(
                    '${widget.batch.totalUnits} units',
                    style: AppTypography.labelLarge.copyWith(
                      color: Colors.white,
                    ),
                  ),
                )
                    .animate()
                    .scaleXY(begin: 0.8, end: 1.0, duration: 400.ms, delay: 500.ms, curve: Curves.easeOutBack)
                    .fadeIn(duration: 400.ms, delay: 500.ms),
              ],
            ),
          )
              .animate()
              .fadeIn(duration: 500.ms)
              .slideY(begin: 0.1, end: 0, duration: 500.ms, curve: Curves.easeOutCubic),

          const SizedBox(height: AppSpacing.lg),

          // Medicine QR codes header
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                'Medicine Strip QR Codes',
                style: AppTypography.titleMedium,
              ),
              Text(
                '${widget.medicines.length} strips',
                style: AppTypography.bodySmall,
              ),
            ],
          ).animate().fadeIn(duration: 400.ms, delay: 400.ms),
          const SizedBox(height: AppSpacing.sm),

          // Medicine QR grid
          GridView.builder(
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
              crossAxisCount: 2,
              crossAxisSpacing: 12,
              mainAxisSpacing: 12,
              childAspectRatio: 0.78,
            ),
            itemCount: widget.medicines.length,
            itemBuilder: (context, index) {
              final medicine = widget.medicines[index];
              final delay = Duration(milliseconds: (500 + index * 40).clamp(500, 1000));
              return Container(
                padding: const EdgeInsets.all(12),
                decoration: AppDecorations.elevatedCard,
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    qrService.generateQRWidget(
                      data: medicine.qrData,
                      size: 120,
                    ),
                    const SizedBox(height: 8),
                    Text(
                      'Strip #${medicine.medicineId}',
                      style: AppTypography.titleSmall,
                      overflow: TextOverflow.ellipsis,
                    ),
                    Text(
                      medicine.medicineName,
                      style: AppTypography.bodySmall,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ],
                ),
              )
                  .animate()
                  .fadeIn(duration: 400.ms, delay: delay)
                  .scaleXY(begin: 0.8, end: 1.0, duration: 400.ms, delay: delay, curve: Curves.easeOutCubic);
            },
          ),

          const SizedBox(height: AppSpacing.lg),

          // Export buttons
          Container(
            decoration: BoxDecoration(
              gradient: _isPrinting ? null : AppGradients.primary,
              borderRadius: BorderRadius.circular(12),
              boxShadow: _isPrinting
                  ? null
                  : [
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
                onPressed: _isPrinting ? null : () => _sharePDF(qrService, batchQRData),
                icon: _isPrinting
                    ? const SizedBox(
                        width: 18,
                        height: 18,
                        child: CircularProgressIndicator(
                          strokeWidth: 2,
                          color: Colors.white,
                        ),
                      )
                    : const Icon(Icons.picture_as_pdf),
                label: Text(_isPrinting ? 'Generating PDF...' : 'Export as PDF'),
                style: ElevatedButton.styleFrom(
                  padding: const EdgeInsets.symmetric(vertical: 14),
                  backgroundColor: Colors.transparent,
                  shadowColor: Colors.transparent,
                  disabledBackgroundColor: AppColors.border,
                ),
              ),
            ),
          ),

          const SizedBox(height: AppSpacing.sm),

          SizedBox(
            width: double.infinity,
            child: OutlinedButton.icon(
              onPressed: _isPrinting ? null : () => _savePDF(qrService, batchQRData),
              icon: const Icon(Icons.save_alt),
              label: const Text('Save to Device'),
              style: OutlinedButton.styleFrom(
                padding: const EdgeInsets.symmetric(vertical: 14),
              ),
            ),
          ),

          const SizedBox(height: AppSpacing.lg),
        ],
      ),
    );
  }

  Future<void> _sharePDF(QRService qrService, String batchQRData) async {
    setState(() => _isPrinting = true);
    try {
      await qrService.sharePDF(
        medicines: widget.medicines,
        batchNumber: widget.batch.batchNumber,
        batchQRData: batchQRData,
      );
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Export failed: $e'),
            backgroundColor: AppColors.error,
            behavior: SnackBarBehavior.floating,
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
          ),
        );
      }
    } finally {
      if (mounted) setState(() => _isPrinting = false);
    }
  }

  Future<void> _printPDF(QRService qrService, String batchQRData) async {
    setState(() => _isPrinting = true);
    try {
      await qrService.printQRCodes(
        medicines: widget.medicines,
        batchNumber: widget.batch.batchNumber,
        batchQRData: batchQRData,
      );
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Print failed: $e'),
            backgroundColor: AppColors.error,
            behavior: SnackBarBehavior.floating,
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
          ),
        );
      }
    } finally {
      if (mounted) setState(() => _isPrinting = false);
    }
  }

  Future<void> _savePDF(QRService qrService, String batchQRData) async {
    setState(() => _isPrinting = true);
    try {
      final path = await qrService.savePDFToFile(
        medicines: widget.medicines,
        batchNumber: widget.batch.batchNumber,
        batchQRData: batchQRData,
      );
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('PDF saved: $path'),
            backgroundColor: AppColors.success,
            behavior: SnackBarBehavior.floating,
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Save failed: $e'),
            backgroundColor: AppColors.error,
            behavior: SnackBarBehavior.floating,
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
          ),
        );
      }
    } finally {
      if (mounted) setState(() => _isPrinting = false);
    }
  }
}
