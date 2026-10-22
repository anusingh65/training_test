import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:provider/provider.dart';
import '../../models/batch_model.dart';
import '../../models/medicine_model.dart';
import '../../services/blockchain_service.dart';
import '../../services/pinata_service.dart';
import '../../config/app_config.dart';
import '../../theme/app_theme.dart';
import '../../widgets/page_route.dart';
import 'qr_viewer_screen.dart';

class RegisterStripsScreen extends StatefulWidget {
  final BatchModel batch;

  const RegisterStripsScreen({super.key, required this.batch});

  @override
  State<RegisterStripsScreen> createState() => _RegisterStripsScreenState();
}

class _RegisterStripsScreenState extends State<RegisterStripsScreen> {
  bool _isRegistering = false;
  int _totalToRegister = 0;
  String _statusMessage = '';
  String? _errorMessage;
  int _uploadedCount = 0;
  int _registeredOnChain = 0;

  Future<void> _registerStrips() async {
    HapticFeedback.mediumImpact();
    setState(() {
      _isRegistering = true;
      _statusMessage = 'Preparing...';
      _errorMessage = null;
      _uploadedCount = 0;
      _registeredOnChain = 0;
      _totalToRegister = widget.batch.totalUnits - widget.batch.registeredUnits;
    });

    try {
      final blockchainService = context.read<BlockchainService>();
      final pinataService = context.read<PinataService>();

      if (blockchainService.credentials == null) {
        throw Exception('Not authenticated. Please login again.');
      }

      final medicines = <MedicineModel>[];
      final startId = widget.batch.batchId * 1000 + widget.batch.registeredUnits + 1;

      setState(() {
        _statusMessage = 'Generating $_totalToRegister medicine entries...';
      });

      for (int i = 0; i < _totalToRegister; i++) {
        medicines.add(MedicineModel(
          medicineId: startId + i,
          batchId: widget.batch.batchId,
          medicineName: widget.batch.medicineName,
          composition: widget.batch.composition,
          dosage: widget.batch.dosage,
          batchNumber: widget.batch.batchNumber,
          manufactureDate: widget.batch.manufactureDate,
          expiryDate: widget.batch.expiryDate,
        ));
      }

      debugPrint('Processing ${medicines.length} medicines in chunks...');

      final chunkSize = AppConfig.bulkRegistrationChunkSize;
      int chunkNumber = 0;

      for (int i = 0; i < medicines.length; i += chunkSize) {
        chunkNumber++;
        final end = (i + chunkSize).clamp(0, medicines.length);
        final chunk = medicines.sublist(i, end);

        setState(() {
          _statusMessage = 'Chunk $chunkNumber: Uploading ${chunk.length} items to IPFS...';
        });

        debugPrint('Uploading chunk $chunkNumber (${chunk.length} items) to Pinata...');

        final ipfsHashes = <String>[];
        final contentHashes = <String>[];

        for (int idx = 0; idx < chunk.length; idx++) {
          final medicine = chunk[idx];

          try {
            final ipfsHash = await pinataService.uploadMedicineMetadata(
              medicine.toJson(),
            );
            final contentHash = pinataService.calculateContentHash(
              medicine.toJson(),
            );

            ipfsHashes.add(ipfsHash);
            contentHashes.add(contentHash);

            setState(() {
              _uploadedCount++;
              _statusMessage = 'Uploaded $_uploadedCount/$_totalToRegister to IPFS';
            });

            debugPrint('Uploaded medicine ${medicine.medicineId}: $ipfsHash');
          } catch (e) {
            debugPrint('IPFS upload failed for ${medicine.medicineId}: $e');
            throw Exception('IPFS upload failed: $e');
          }
        }

        setState(() {
          _statusMessage = 'Chunk $chunkNumber: Sending to blockchain...';
        });

        debugPrint('Registering chunk $chunkNumber on blockchain...');

        try {
          final txHash = await blockchainService.addMedicinesToBatch(
            batchId: widget.batch.batchId,
            medicineIds: chunk.map((m) => m.medicineId).toList(),
            ipfsHashes: ipfsHashes,
            contentHashes: contentHashes,
          );

          debugPrint('Transaction sent: $txHash');

          setState(() {
            _statusMessage = 'Chunk $chunkNumber: Waiting for confirmation...\nTx: ${txHash.substring(0, 10)}...';
          });

          final receipt = await blockchainService.waitForTransaction(txHash);

          if (receipt == null) {
            throw Exception('Transaction timeout. Please check Sepolia explorer.');
          }

          if (!receipt.status!) {
            throw Exception('Transaction failed on blockchain');
          }

          setState(() {
            _registeredOnChain += chunk.length;
            _statusMessage = 'Chunk $chunkNumber: Confirmed! ($_registeredOnChain/$_totalToRegister total)';
          });

          debugPrint('Chunk $chunkNumber confirmed! Receipt: ${receipt.blockNumber}');
        } catch (e) {
          debugPrint('Blockchain error: $e');
          throw Exception('Blockchain registration failed: $e');
        }

        await Future.delayed(const Duration(milliseconds: 500));
      }

      debugPrint('All chunks processed successfully!');

      if (mounted) {
        HapticFeedback.heavyImpact();
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('All $_totalToRegister strips registered!'),
            backgroundColor: AppColors.success,
            duration: const Duration(seconds: 3),
            behavior: SnackBarBehavior.floating,
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
          ),
        );

        Navigator.pushReplacement(
          context,
          FadeSlideRoute(
            page: QRViewerScreen(
              batch: widget.batch.copyWith(
                registeredUnits: widget.batch.totalUnits,
                isComplete: true,
              ),
              medicines: medicines,
            ),
          ),
        );
      }
    } catch (e) {
      debugPrint('Registration error: $e');
      setState(() {
        _errorMessage = e.toString();
        _statusMessage = 'Registration stopped';
        _isRegistering = false;
      });

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Error: ${e.toString()}'),
            backgroundColor: AppColors.error,
            duration: const Duration(seconds: 5),
            behavior: SnackBarBehavior.floating,
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
          ),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Register Strips', style: AppTypography.titleLarge),
      ),
      body: Padding(
        padding: const EdgeInsets.all(AppSpacing.lg),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            if (!_isRegistering) ...[
              // Pre-registration state
              Container(
                width: 80,
                height: 80,
                decoration: BoxDecoration(
                  gradient: AppGradients.primary,
                  borderRadius: BorderRadius.circular(20),
                  boxShadow: [
                    BoxShadow(
                      color: AppColors.primary.withValues(alpha: 0.3),
                      blurRadius: 20,
                      offset: const Offset(0, 8),
                    ),
                  ],
                ),
                child: const Icon(Icons.qr_code_2, size: 40, color: Colors.white),
              )
                  .animate(onPlay: (c) => c.repeat(reverse: true))
                  .scaleXY(begin: 1.0, end: 1.05, duration: 2000.ms, curve: Curves.easeInOut)
                  .animate()
                  .fadeIn(duration: 500.ms)
                  .scaleXY(begin: 0.5, end: 1.0, duration: 500.ms, curve: Curves.easeOutBack),
              const SizedBox(height: AppSpacing.lg),
              Text(
                'Ready to register ${widget.batch.totalUnits - widget.batch.registeredUnits} strips',
                style: AppTypography.titleLarge,
                textAlign: TextAlign.center,
              ).animate().fadeIn(duration: 500.ms, delay: 200.ms),
              const SizedBox(height: AppSpacing.md),

              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  _buildBulletItem('Generate unique IDs', 0),
                  _buildBulletItem('Upload metadata to IPFS', 1),
                  _buildBulletItem('Register on blockchain', 2),
                  _buildBulletItem('Generate QR codes', 3),
                ],
              ),

              const SizedBox(height: AppSpacing.xl),
              SizedBox(
                width: double.infinity,
                child: Container(
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
                  child: ElevatedButton.icon(
                    onPressed: _registerStrips,
                    icon: const Icon(Icons.play_arrow),
                    label: const Text('Start Registration'),
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
            ] else ...[
              // Progress state
              SizedBox(
                width: 80,
                height: 80,
                child: TweenAnimationBuilder<double>(
                  tween: Tween(begin: 0, end: _totalToRegister > 0 ? _registeredOnChain / _totalToRegister : 0),
                  duration: const Duration(milliseconds: 500),
                  curve: Curves.easeOutCubic,
                  builder: (context, value, _) {
                    return CircularProgressIndicator(
                      value: _totalToRegister > 0 ? value : null,
                      strokeWidth: 5,
                      backgroundColor: AppColors.border,
                      color: AppColors.primary,
                    );
                  },
                ),
              ),
              const SizedBox(height: AppSpacing.xl),

              AnimatedSwitcher(
                duration: const Duration(milliseconds: 300),
                child: Text(
                  _statusMessage,
                  key: ValueKey(_statusMessage),
                  style: AppTypography.titleSmall,
                  textAlign: TextAlign.center,
                ),
              ),
              const SizedBox(height: AppSpacing.lg),

              // Stat chips
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                children: [
                  _buildStatChip('IPFS', _uploadedCount, _totalToRegister, AppColors.info),
                  _buildStatChip('Chain', _registeredOnChain, _totalToRegister, AppColors.success),
                ],
              ),
              const SizedBox(height: AppSpacing.lg),

              // Progress bar
              ClipRRect(
                borderRadius: BorderRadius.circular(4),
                child: TweenAnimationBuilder<double>(
                  tween: Tween(begin: 0, end: _totalToRegister > 0 ? _registeredOnChain / _totalToRegister : 0),
                  duration: const Duration(milliseconds: 500),
                  curve: Curves.easeOutCubic,
                  builder: (context, value, _) {
                    return LinearProgressIndicator(
                      value: value,
                      minHeight: 8,
                      backgroundColor: AppColors.border,
                      color: AppColors.primary,
                    );
                  },
                ),
              ),
              const SizedBox(height: AppSpacing.sm),
              Text(
                '$_registeredOnChain / $_totalToRegister confirmed on blockchain',
                style: AppTypography.bodyMedium,
              ),

              // Error message
              if (_errorMessage != null) ...[
                const SizedBox(height: AppSpacing.lg),
                Container(
                  padding: const EdgeInsets.all(AppSpacing.md),
                  decoration: BoxDecoration(
                    color: const Color(0xFFFEF2F2),
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: const Color(0xFFFECACA)),
                  ),
                  child: Column(
                    children: [
                      Row(
                        children: [
                          const Icon(Icons.error_outline, color: AppColors.error, size: 20),
                          const SizedBox(width: AppSpacing.sm),
                          Expanded(
                            child: Text(
                              'Error Occurred',
                              style: AppTypography.titleSmall.copyWith(color: AppColors.error),
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: AppSpacing.sm),
                      Align(
                        alignment: Alignment.centerLeft,
                        child: Text(
                          _errorMessage!,
                          style: AppTypography.bodySmall.copyWith(color: AppColors.error),
                        ),
                      ),
                      const SizedBox(height: AppSpacing.md),
                      SizedBox(
                        width: double.infinity,
                        child: OutlinedButton(
                          onPressed: () => Navigator.pop(context),
                          style: OutlinedButton.styleFrom(
                            foregroundColor: AppColors.error,
                            side: const BorderSide(color: AppColors.error),
                          ),
                          child: const Text('Go Back'),
                        ),
                      ),
                    ],
                  ),
                )
                    .animate()
                    .fadeIn(duration: 300.ms)
                    .slideY(begin: -0.1, end: 0, duration: 300.ms)
                    .shake(hz: 2, duration: 400.ms, delay: 100.ms),
              ],
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildBulletItem(String text, int index) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        children: [
          Container(
            width: 6,
            height: 6,
            decoration: const BoxDecoration(
              shape: BoxShape.circle,
              color: AppColors.primary,
            ),
          ),
          const SizedBox(width: AppSpacing.sm),
          Text(text, style: AppTypography.bodyLarge),
        ],
      ),
    )
        .animate()
        .fadeIn(duration: 400.ms, delay: Duration(milliseconds: 300 + index * 100))
        .slideX(begin: 0.2, end: 0, duration: 400.ms, delay: Duration(milliseconds: 300 + index * 100));
  }

  Widget _buildStatChip(String label, int current, int total, Color color) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 10),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [color.withValues(alpha: 0.1), color.withValues(alpha: 0.05)],
        ),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: color.withValues(alpha: 0.3)),
      ),
      child: Column(
        children: [
          Text(
            label,
            style: AppTypography.bodySmall.copyWith(
              color: color,
              fontWeight: FontWeight.w600,
            ),
          ),
          const SizedBox(height: 2),
          TweenAnimationBuilder<int>(
            tween: IntTween(begin: 0, end: current),
            duration: const Duration(milliseconds: 500),
            builder: (context, val, _) {
              return Text(
                '$val/$total',
                style: AppTypography.titleMedium.copyWith(color: color),
              );
            },
          ),
        ],
      ),
    );
  }
}
