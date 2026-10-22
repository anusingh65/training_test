import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:mobile_scanner/mobile_scanner.dart';
import '../../theme/app_theme.dart';
import '../../widgets/page_route.dart';
import 'scan_result_screen.dart';

class QRScannerScreen extends StatefulWidget {
  const QRScannerScreen({super.key});

  @override
  State<QRScannerScreen> createState() => _QRScannerScreenState();
}

class _QRScannerScreenState extends State<QRScannerScreen> {
  final MobileScannerController _controller = MobileScannerController(
    detectionSpeed: DetectionSpeed.normal,
    facing: CameraFacing.back,
  );
  bool _isProcessing = false;

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  void _onDetect(BarcodeCapture capture) {
    if (_isProcessing) return;

    final barcode = capture.barcodes.firstOrNull;
    if (barcode == null || barcode.rawValue == null) return;

    setState(() => _isProcessing = true);
    HapticFeedback.mediumImpact();

    try {
      final data = jsonDecode(barcode.rawValue!) as Map<String, dynamic>;

      // Validate QR structure
      if (data['type'] != 'batch') {
        _showError('Invalid QR: Expected batch type, got "${data['type']}"');
        return;
      }

      if (data['network'] != 'sepolia') {
        _showError('Invalid QR: Wrong network "${data['network']}"');
        return;
      }

      final batchId = data['id'] as int?;
      if (batchId == null || batchId <= 0) {
        _showError('Invalid QR: Missing batch ID');
        return;
      }

      // Navigate to scan result
      Navigator.of(context).pushReplacement(
        FadeSlideRoute(
          page: ScanResultScreen(
            batchId: batchId,
            batchNumber: data['number']?.toString() ?? 'Unknown',
            totalUnits: data['units'] as int? ?? 0,
            qrData: data,
          ),
        ),
      );
    } on FormatException {
      _showError('Invalid QR code format. Expected JSON batch data.');
    } catch (e) {
      _showError('Error processing QR: $e');
    }
  }

  void _showError(String message) {
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: AppColors.error,
        behavior: SnackBarBehavior.floating,
      ),
    );
    Future.delayed(const Duration(seconds: 2), () {
      if (mounted) setState(() => _isProcessing = false);
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black,
      body: Stack(
        children: [
          // Camera
          MobileScanner(
            controller: _controller,
            onDetect: _onDetect,
          ),

          // Overlay
          Container(
            decoration: BoxDecoration(
              color: Colors.black.withValues(alpha: 0.5),
            ),
          ),

          // Scan Frame
          Center(
            child: Container(
              width: 280,
              height: 280,
              decoration: BoxDecoration(
                border: Border.all(color: AppColors.primary, width: 3),
                borderRadius: BorderRadius.circular(20),
              ),
            )
                .animate(onPlay: (c) => c.repeat(reverse: true))
                .scaleXY(begin: 1.0, end: 1.02, duration: 1500.ms, curve: Curves.easeInOut),
          ),

          // Scanning line animation
          Center(
            child: SizedBox(
              width: 260,
              height: 260,
              child: Align(
                alignment: Alignment.topCenter,
                child: Container(
                  width: 260,
                  height: 2,
                  decoration: BoxDecoration(
                    gradient: LinearGradient(
                      colors: [
                        Colors.transparent,
                        AppColors.primary.withValues(alpha: 0.8),
                        Colors.transparent,
                      ],
                    ),
                  ),
                )
                    .animate(onPlay: (c) => c.repeat())
                    .slideY(begin: 0, end: 130, duration: 2000.ms, curve: Curves.easeInOut)
                    .then()
                    .slideY(begin: 130, end: 0, duration: 2000.ms, curve: Curves.easeInOut),
              ),
            ),
          ),

          // Top bar
          SafeArea(
            child: Padding(
              padding: const EdgeInsets.all(AppSpacing.md),
              child: Row(
                children: [
                  GestureDetector(
                    onTap: () => Navigator.of(context).pop(),
                    child: Container(
                      width: 40,
                      height: 40,
                      decoration: BoxDecoration(
                        color: Colors.white.withValues(alpha: 0.2),
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: const Icon(Icons.arrow_back, color: Colors.white, size: 20),
                    ),
                  ),
                  const Spacer(),
                  GestureDetector(
                    onTap: () => _controller.toggleTorch(),
                    child: Container(
                      width: 40,
                      height: 40,
                      decoration: BoxDecoration(
                        color: Colors.white.withValues(alpha: 0.2),
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: const Icon(Icons.flash_on, color: Colors.white, size: 20),
                    ),
                  ),
                ],
              ),
            ),
          ),

          // Bottom instructions
          Positioned(
            bottom: 80,
            left: 0,
            right: 0,
            child: Column(
              children: [
                Text(
                  'Scan Batch QR Code',
                  style: AppTypography.titleMedium.copyWith(color: Colors.white),
                ),
                const SizedBox(height: 4),
                Text(
                  'Align the QR code within the frame',
                  style: AppTypography.bodySmall.copyWith(color: Colors.white70),
                ),
                if (_isProcessing) ...[
                  const SizedBox(height: 16),
                  const SizedBox(
                    width: 24,
                    height: 24,
                    child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                  ),
                ],
              ],
            ).animate().fadeIn(duration: 600.ms, delay: 300.ms),
          ),
        ],
      ),
    );
  }
}
