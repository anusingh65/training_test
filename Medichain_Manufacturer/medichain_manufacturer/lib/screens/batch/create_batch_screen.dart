import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:provider/provider.dart';
import 'package:intl/intl.dart';
import '../../models/batch_model.dart';
import '../../models/drug_model.dart';
import '../../services/blockchain_service.dart';
import '../../services/pinata_service.dart';
import '../../services/private_key_wallet_service.dart';
import '../../services/supabase_service.dart';
import '../../config/app_config.dart';
import '../../theme/app_theme.dart';

class CreateBatchScreen extends StatefulWidget {
  const CreateBatchScreen({super.key});

  @override
  State<CreateBatchScreen> createState() => _CreateBatchScreenState();
}

class _CreateBatchScreenState extends State<CreateBatchScreen> {
  final _formKey = GlobalKey<FormState>();

  final _batchNumberController = TextEditingController();
  final _totalUnitsController = TextEditingController();

  DrugModel? _selectedDrug;
  late DateTime _manufactureDate;

  bool _isSubmitting = false;
  String? _errorMessage;

  int _currentStep = 0;
  static const _totalSteps = 2;
  final _stepLabels = const ['Batch Info', 'Drug Selection'];

  @override
  void initState() {
    super.initState();
    final now = DateTime.now();
    _manufactureDate = DateTime(now.year, now.month, now.day);
  }

  @override
  void dispose() {
    _batchNumberController.dispose();
    _totalUnitsController.dispose();
    super.dispose();
  }

  bool _validateCurrentStep() {
    switch (_currentStep) {
      case 0:
        if (_batchNumberController.text.trim().isEmpty) {
          setState(() => _errorMessage = 'Please enter batch number');
          return false;
        }
        final units = int.tryParse(_totalUnitsController.text.trim());
        if (units == null || units <= 0) {
          setState(() => _errorMessage = 'Please enter a valid number of units');
          return false;
        }
        if (units > AppConfig.maxBatchSize) {
          setState(() => _errorMessage = 'Maximum batch size is ${AppConfig.maxBatchSize}');
          return false;
        }
        break;
      case 1:
        if (_selectedDrug == null) {
          setState(() => _errorMessage = 'Please select a drug');
          return false;
        }
        break;
    }
    setState(() => _errorMessage = null);
    return true;
  }

  void _validateAndNext() {
    if (!_validateCurrentStep()) return;
    HapticFeedback.lightImpact();
    if (_currentStep < _totalSteps - 1) {
      setState(() => _currentStep++);
    }
  }

  void _goBack() {
    if (_currentStep > 0) {
      HapticFeedback.lightImpact();
      setState(() {
        _currentStep--;
        _errorMessage = null;
      });
    }
  }

  Future<void> _submitForm() async {
    if (!_validateCurrentStep()) return;

    setState(() {
      _isSubmitting = true;
      _errorMessage = null;
    });

    try {
      final walletService = context.read<PrivateKeyWalletService>();
      final blockchainService = context.read<BlockchainService>();
      final pinataService = context.read<PinataService>();
      final supabaseService = context.read<SupabaseService>();

      final manufacturer = supabaseService.manufacturer!;
      final drug = _selectedDrug!;
      final expiryDate = drug.calculateExpiryDate(_manufactureDate);

      final batchId = DateTime.now().millisecondsSinceEpoch ~/ 1000;

      final batch = BatchModel(
        batchId: batchId,
        batchNumber: _batchNumberController.text,
        totalUnits: int.parse(_totalUnitsController.text),
        manufacturer: walletService.address!,
        medicineName: drug.name,
        composition: drug.composition,
        dosage: drug.dosage,
        manufactureDate: _manufactureDate,
        expiryDate: expiryDate,
        manufacturerName: manufacturer.name,
        manufacturerLicense: manufacturer.license,
        manufacturerLocation: manufacturer.location,
        pillsPerStrip: drug.pillsPerStrip,
      );

      final ipfsHash = await pinataService.uploadBatchMetadata(batch.toJson());
      final contentHash = pinataService.calculateContentHash(batch.toJson());

      final txHash = await blockchainService.createBatch(
        batchId: batchId,
        batchNumber: batch.batchNumber,
        totalUnits: batch.totalUnits,
        ipfsHash: ipfsHash,
        contentHash: contentHash,
      );

      await blockchainService.waitForTransaction(txHash);

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: const Text('Batch created successfully!'),
            backgroundColor: AppColors.success,
            behavior: SnackBarBehavior.floating,
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
          ),
        );
        Navigator.pop(context, true);
      }
    } catch (e) {
      setState(() {
        _errorMessage = 'Failed to create batch: ${e.toString()}';
        _isSubmitting = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final supabaseService = context.watch<SupabaseService>();

    return Scaffold(
      appBar: AppBar(
        title: Text('Create Batch', style: AppTypography.titleLarge),
      ),
      body: Form(
        key: _formKey,
        child: Column(
          children: [
            // Demo mode banner
            if (supabaseService.isDemoMode)
              Container(
                width: double.infinity,
                padding: const EdgeInsets.symmetric(vertical: 6, horizontal: AppSpacing.md),
                color: AppColors.info.withValues(alpha: 0.1),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Icon(Icons.science_outlined, size: 14, color: AppColors.info),
                    const SizedBox(width: 6),
                    Text(
                      'Demo Mode - Using sample data',
                      style: AppTypography.bodySmall.copyWith(color: AppColors.info),
                    ),
                  ],
                ),
              ),

            // Step indicator
            _buildStepIndicator(),

            // Step content
            Expanded(
              child: AnimatedSwitcher(
                duration: const Duration(milliseconds: 300),
                transitionBuilder: (child, animation) {
                  return FadeTransition(
                    opacity: animation,
                    child: SlideTransition(
                      position: Tween<Offset>(
                        begin: const Offset(0.1, 0),
                        end: Offset.zero,
                      ).animate(CurvedAnimation(
                        parent: animation,
                        curve: Curves.easeOutCubic,
                      )),
                      child: child,
                    ),
                  );
                },
                child: SingleChildScrollView(
                  key: ValueKey(_currentStep),
                  padding: const EdgeInsets.all(AppSpacing.lg),
                  child: _buildStepContent(),
                ),
              ),
            ),

            // Error message
            if (_errorMessage != null)
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: AppSpacing.lg),
                child: Container(
                  width: double.infinity,
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: const Color(0xFFFEF2F2),
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: const Color(0xFFFECACA)),
                  ),
                  child: Row(
                    children: [
                      const Icon(Icons.error_outline, color: AppColors.error, size: 18),
                      const SizedBox(width: AppSpacing.sm),
                      Expanded(
                        child: Text(
                          _errorMessage!,
                          style: AppTypography.bodySmall.copyWith(color: AppColors.error),
                        ),
                      ),
                    ],
                  ),
                ),
              )
                  .animate()
                  .fadeIn(duration: 300.ms)
                  .shake(hz: 3, duration: 400.ms),

            // Bottom navigation
            _buildBottomNav(),
          ],
        ),
      ),
    );
  }

  Widget _buildStepIndicator() {
    return Container(
      padding: const EdgeInsets.symmetric(vertical: AppSpacing.md, horizontal: AppSpacing.lg),
      decoration: const BoxDecoration(
        color: AppColors.surface,
        border: Border(bottom: BorderSide(color: AppColors.border)),
      ),
      child: Row(
        children: List.generate(_totalSteps * 2 - 1, (i) {
          if (i.isOdd) {
            final stepBefore = i ~/ 2;
            return Expanded(
              child: TweenAnimationBuilder<double>(
                tween: Tween(begin: 0, end: stepBefore < _currentStep ? 1.0 : 0.0),
                duration: const Duration(milliseconds: 400),
                curve: Curves.easeInOut,
                builder: (context, value, _) {
                  return Container(
                    height: 2,
                    decoration: BoxDecoration(
                      gradient: LinearGradient(
                        colors: [
                          AppColors.primary,
                          Color.lerp(AppColors.primary, AppColors.border, 1 - value)!,
                        ],
                      ),
                    ),
                  );
                },
              ),
            );
          }
          final step = i ~/ 2;
          final isActive = step == _currentStep;
          final isCompleted = step < _currentStep;

          return Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              AnimatedContainer(
                duration: const Duration(milliseconds: 300),
                curve: Curves.easeOutCubic,
                width: 32,
                height: 32,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  gradient: isCompleted || isActive ? AppGradients.primary : null,
                  color: isCompleted || isActive ? null : AppColors.background,
                  border: isCompleted || isActive
                      ? null
                      : Border.all(color: AppColors.border, width: 2),
                  boxShadow: isActive
                      ? [
                          BoxShadow(
                            color: AppColors.primary.withValues(alpha: 0.3),
                            blurRadius: 8,
                            offset: const Offset(0, 2),
                          ),
                        ]
                      : null,
                ),
                child: Center(
                  child: isCompleted
                      ? const Icon(Icons.check, size: 16, color: Colors.white)
                      : Text(
                          '${step + 1}',
                          style: TextStyle(
                            fontSize: 13,
                            fontWeight: FontWeight.w600,
                            fontFamily: 'Inter',
                            color: isActive ? Colors.white : AppColors.textTertiary,
                          ),
                        ),
                ),
              ),
              const SizedBox(height: 4),
              AnimatedDefaultTextStyle(
                duration: const Duration(milliseconds: 300),
                style: AppTypography.bodySmall.copyWith(
                  color: isActive || isCompleted ? AppColors.primary : AppColors.textTertiary,
                  fontWeight: isActive ? FontWeight.w600 : FontWeight.w400,
                ),
                child: Text(_stepLabels[step]),
              ),
            ],
          );
        }),
      ),
    );
  }

  Widget _buildStepContent() {
    switch (_currentStep) {
      case 0:
        return _buildStep0();
      case 1:
        return _buildStep1();
      default:
        return const SizedBox();
    }
  }

  Widget _buildStep0() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text('Batch Information', style: AppTypography.titleLarge)
            .animate().fadeIn(duration: 400.ms).slideY(begin: 0.2, end: 0, duration: 400.ms),
        const SizedBox(height: AppSpacing.xs),
        Text('Enter the basic batch details', style: AppTypography.bodyMedium)
            .animate().fadeIn(duration: 400.ms, delay: 50.ms),
        const SizedBox(height: AppSpacing.lg),
        TextFormField(
          controller: _batchNumberController,
          decoration: const InputDecoration(
            labelText: 'Batch Number',
            hintText: 'e.g., BATCH-2026-001',
          ),
        ).animate().fadeIn(duration: 400.ms, delay: 100.ms).slideY(begin: 0.2, end: 0, duration: 400.ms, delay: 100.ms),
        const SizedBox(height: AppSpacing.md),
        TextFormField(
          controller: _totalUnitsController,
          decoration: const InputDecoration(
            labelText: 'Total Units (Strips)',
            hintText: 'e.g., 1000',
          ),
          keyboardType: TextInputType.number,
        ).animate().fadeIn(duration: 400.ms, delay: 200.ms).slideY(begin: 0.2, end: 0, duration: 400.ms, delay: 200.ms),
      ],
    );
  }

  Widget _buildStep1() {
    final supabaseService = context.read<SupabaseService>();
    final drugs = supabaseService.drugs;
    final dateFormat = DateFormat('MMM dd, yyyy');

    if (drugs.isEmpty) {
      return Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('Select Drug', style: AppTypography.titleLarge),
          const SizedBox(height: AppSpacing.lg),
          Container(
            padding: const EdgeInsets.all(AppSpacing.lg),
            decoration: BoxDecoration(
              color: AppColors.warning.withValues(alpha: 0.08),
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: AppColors.warning.withValues(alpha: 0.3)),
            ),
            child: Row(
              children: [
                const Icon(Icons.warning_amber_rounded, color: AppColors.warning),
                const SizedBox(width: AppSpacing.sm),
                Expanded(
                  child: Text(
                    'No drugs authorized for this manufacturer. Contact admin.',
                    style: AppTypography.bodyMedium.copyWith(color: AppColors.warning),
                  ),
                ),
              ],
            ),
          ),
        ],
      );
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text('Select Drug', style: AppTypography.titleLarge)
            .animate().fadeIn(duration: 400.ms).slideY(begin: 0.2, end: 0, duration: 400.ms),
        const SizedBox(height: AppSpacing.xs),
        Text('Choose from your authorized drug catalog', style: AppTypography.bodyMedium)
            .animate().fadeIn(duration: 400.ms, delay: 50.ms),
        const SizedBox(height: AppSpacing.lg),

        DropdownButtonFormField<DrugModel>(
          decoration: const InputDecoration(
            labelText: 'Drug',
            hintText: 'Select a drug',
          ),
          value: _selectedDrug,
          isExpanded: true,
          items: drugs.map((drug) {
            return DropdownMenuItem<DrugModel>(
              value: drug,
              child: Text(drug.name),
            );
          }).toList(),
          onChanged: (drug) {
            HapticFeedback.selectionClick();
            setState(() {
              _selectedDrug = drug;
            });
          },
        ).animate().fadeIn(duration: 400.ms, delay: 100.ms).slideY(begin: 0.2, end: 0, duration: 400.ms, delay: 100.ms),

        const SizedBox(height: AppSpacing.md),

        if (_selectedDrug != null) ...[
          _buildReadOnlyField('Composition', _selectedDrug!.composition)
              .animate().fadeIn(duration: 300.ms, delay: 0.ms).slideY(begin: 0.15, end: 0, duration: 300.ms),
          const SizedBox(height: AppSpacing.sm),
          _buildReadOnlyField('Dosage', _selectedDrug!.dosage)
              .animate().fadeIn(duration: 300.ms, delay: 80.ms).slideY(begin: 0.15, end: 0, duration: 300.ms, delay: 80.ms),
          const SizedBox(height: AppSpacing.sm),
          _buildReadOnlyField('Pills per Strip', _selectedDrug!.pillsPerStrip.toString())
              .animate().fadeIn(duration: 300.ms, delay: 160.ms).slideY(begin: 0.15, end: 0, duration: 300.ms, delay: 160.ms),
          const SizedBox(height: AppSpacing.md),

          Row(
            children: [
              Expanded(
                child: _buildReadOnlyField(
                  'Manufacture Date',
                  dateFormat.format(_manufactureDate),
                ),
              ),
              const SizedBox(width: AppSpacing.md),
              Expanded(
                child: _buildReadOnlyField(
                  'Expiry Date',
                  dateFormat.format(
                    _selectedDrug!.calculateExpiryDate(_manufactureDate),
                  ),
                ),
              ),
            ],
          ).animate().fadeIn(duration: 300.ms, delay: 240.ms).slideY(begin: 0.15, end: 0, duration: 300.ms, delay: 240.ms),
          const SizedBox(height: AppSpacing.sm),
          Text(
            'Expires ${_selectedDrug!.expiryFromManufacture} months from manufacture',
            style: AppTypography.bodySmall,
          ).animate().fadeIn(duration: 300.ms, delay: 320.ms),
        ],
      ],
    );
  }

  Widget _buildReadOnlyField(String label, String value) {
    return InputDecorator(
      decoration: InputDecoration(
        labelText: label,
        filled: true,
        fillColor: AppColors.background,
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: AppColors.border),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: AppColors.border),
        ),
      ),
      child: Text(value, style: AppTypography.bodyLarge),
    );
  }

  Widget _buildBottomNav() {
    final isLastStep = _currentStep == _totalSteps - 1;

    return Container(
      padding: const EdgeInsets.all(AppSpacing.md),
      decoration: const BoxDecoration(
        color: AppColors.surface,
        border: Border(top: BorderSide(color: AppColors.border)),
      ),
      child: SafeArea(
        top: false,
        child: Row(
          children: [
            if (_currentStep > 0)
              Expanded(
                child: OutlinedButton(
                  onPressed: _isSubmitting ? null : _goBack,
                  style: OutlinedButton.styleFrom(
                    padding: const EdgeInsets.symmetric(vertical: 14),
                  ),
                  child: const Text('Back'),
                ),
              ),
            if (_currentStep > 0) const SizedBox(width: AppSpacing.sm),
            Expanded(
              child: Container(
                decoration: BoxDecoration(
                  gradient: _isSubmitting ? null : AppGradients.primary,
                  borderRadius: BorderRadius.circular(12),
                  boxShadow: _isSubmitting
                      ? null
                      : [
                          BoxShadow(
                            color: AppColors.primary.withValues(alpha: 0.3),
                            blurRadius: 8,
                            offset: const Offset(0, 3),
                          ),
                        ],
                ),
                child: ElevatedButton(
                  onPressed: _isSubmitting
                      ? null
                      : isLastStep
                          ? _submitForm
                          : _validateAndNext,
                  style: ElevatedButton.styleFrom(
                    padding: const EdgeInsets.symmetric(vertical: 14),
                    backgroundColor: Colors.transparent,
                    shadowColor: Colors.transparent,
                    disabledBackgroundColor: AppColors.border,
                  ),
                  child: _isSubmitting
                      ? const SizedBox(
                          height: 20,
                          width: 20,
                          child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                        )
                      : Text(isLastStep ? 'Create Batch' : 'Continue'),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
