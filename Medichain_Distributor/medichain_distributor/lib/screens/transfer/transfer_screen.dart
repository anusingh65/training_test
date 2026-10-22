import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:provider/provider.dart';
import '../../config/app_config.dart';
import '../../services/blockchain_service.dart';
import '../../services/private_key_wallet_service.dart';
import '../../theme/app_theme.dart';

class TransferScreen extends StatefulWidget {
  final int batchId;
  final List<int> medicineIds;

  const TransferScreen({
    super.key,
    required this.batchId,
    required this.medicineIds,
  });

  @override
  State<TransferScreen> createState() => _TransferScreenState();
}

class _TransferScreenState extends State<TransferScreen> {
  final _addressController = TextEditingController();
  bool _isValidating = false;
  bool _isTransferring = false;
  bool _transferComplete = false;
  String? _error;
  String? _recipientName;
  String? _recipientLocation;
  int? _recipientRole;
  String? _txHash;

  @override
  void dispose() {
    _addressController.dispose();
    super.dispose();
  }

  Future<void> _validateRecipient() async {
    final address = _addressController.text.trim();
    if (address.isEmpty || address.length != 42 || !address.startsWith('0x')) {
      setState(() => _error = 'Enter a valid Ethereum address (0x...)');
      return;
    }

    // Check not self-transfer
    final walletService = context.read<PrivateKeyWalletService>();
    if (address.toLowerCase() == walletService.address?.toLowerCase()) {
      setState(() => _error = 'Cannot transfer to yourself');
      return;
    }

    setState(() {
      _isValidating = true;
      _error = null;
      _recipientName = null;
    });

    try {
      final blockchainService = context.read<BlockchainService>();

      // Check role
      final role = await blockchainService.getUserRole(address);
      if (role != AppConfig.roleDistributor && role != AppConfig.rolePharmacy) {
        setState(() {
          _error = 'Recipient must be a Distributor or Pharmacy. Got: ${AppConfig.roleName(role)}';
          _isValidating = false;
        });
        return;
      }

      // Check whitelist
      final whitelisted = await blockchainService.isWhitelisted(address);
      if (!whitelisted) {
        setState(() {
          _error = 'Recipient is not whitelisted on the blockchain';
          _isValidating = false;
        });
        return;
      }

      // Get info
      final actorInfo = await blockchainService.getActorInfo(address);

      if (mounted) {
        setState(() {
          _recipientName = actorInfo?['name'] ?? 'Unknown';
          _recipientLocation = actorInfo?['location'] ?? 'Unknown';
          _recipientRole = role;
          _isValidating = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _error = 'Validation failed: $e';
          _isValidating = false;
        });
      }
    }
  }

  Future<void> _executeTransfer() async {
    setState(() {
      _isTransferring = true;
      _error = null;
    });
    HapticFeedback.mediumImpact();

    try {
      final blockchainService = context.read<BlockchainService>();

      final txHash = await blockchainService.transferBatch(
        widget.medicineIds,
        _addressController.text.trim(),
      );

      if (mounted) {
        setState(() {
          _txHash = txHash;
          _transferComplete = true;
          _isTransferring = false;
        });
        HapticFeedback.heavyImpact();
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _error = 'Transfer failed: $e';
          _isTransferring = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(title: const Text('Transfer Batch')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(AppSpacing.md),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Transfer success banner
            if (_transferComplete)
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(20),
                decoration: AppDecorations.gradientCard(
                  [AppColors.primaryGradientStart, AppColors.primaryGradientEnd],
                ),
                child: Column(
                  children: [
                    const Icon(Icons.check_circle_outline, color: Colors.white, size: 48),
                    const SizedBox(height: 12),
                    Text(
                      'Transfer Complete!',
                      style: AppTypography.titleLarge.copyWith(color: Colors.white),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      '${widget.medicineIds.length} medicines transferred',
                      style: AppTypography.bodyMedium.copyWith(color: Colors.white70),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      'Tx: ${_txHash?.substring(0, 10)}...${_txHash?.substring(_txHash!.length - 6)}',
                      style: AppTypography.mono.copyWith(color: Colors.white70, fontSize: 11),
                    ),
                  ],
                ),
              )
                  .animate()
                  .fadeIn(duration: 600.ms)
                  .scaleXY(begin: 0.9, end: 1.0, duration: 600.ms, curve: Curves.easeOutBack),

            if (_transferComplete) const SizedBox(height: 16),

            // Batch info
            Container(
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
                          color: AppColors.primaryLight,
                          borderRadius: BorderRadius.circular(10),
                        ),
                        child: const Icon(Icons.inventory_2, color: AppColors.primary, size: 20),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text('Batch #${widget.batchId}', style: AppTypography.titleMedium),
                            Text('${widget.medicineIds.length} medicines to transfer', style: AppTypography.bodySmall),
                          ],
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            )
                .animate()
                .fadeIn(duration: 500.ms)
                .slideY(begin: 0.05, end: 0, duration: 500.ms),

            const SizedBox(height: AppSpacing.lg),

            if (!_transferComplete) ...[
              // Recipient address input
              Text('Recipient Address', style: AppTypography.titleSmall)
                  .animate()
                  .fadeIn(duration: 500.ms, delay: 100.ms),
              const SizedBox(height: 8),

              TextField(
                controller: _addressController,
                decoration: InputDecoration(
                  hintText: '0x...',
                  prefixIcon: const Icon(Icons.account_balance_wallet_outlined, size: 20),
                  suffixIcon: _isValidating
                      ? const Padding(
                          padding: EdgeInsets.all(12),
                          child: SizedBox(
                            width: 20,
                            height: 20,
                            child: CircularProgressIndicator(strokeWidth: 2, color: AppColors.primary),
                          ),
                        )
                      : IconButton(
                          icon: const Icon(Icons.search, size: 20),
                          onPressed: _validateRecipient,
                        ),
                ),
                enabled: !_isTransferring,
                onSubmitted: (_) => _validateRecipient(),
              )
                  .animate()
                  .fadeIn(duration: 500.ms, delay: 150.ms),

              const SizedBox(height: 12),

              // Validate button
              SizedBox(
                width: double.infinity,
                child: OutlinedButton.icon(
                  onPressed: _isValidating || _isTransferring ? null : _validateRecipient,
                  icon: const Icon(Icons.verified_user_outlined, size: 18),
                  label: const Text('Validate Recipient'),
                ),
              )
                  .animate()
                  .fadeIn(duration: 500.ms, delay: 200.ms),

              // Error
              if (_error != null) ...[
                const SizedBox(height: 12),
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: const Color(0xFFFEF2F2),
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: const Color(0xFFFECACA)),
                  ),
                  child: Row(
                    children: [
                      const Icon(Icons.error_outline, color: AppColors.error, size: 18),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Text(
                          _error!,
                          style: AppTypography.bodySmall.copyWith(color: AppColors.error),
                        ),
                      ),
                    ],
                  ),
                )
                    .animate()
                    .fadeIn(duration: 300.ms)
                    .shake(hz: 3, duration: 400.ms),
              ],

              // Recipient info
              if (_recipientName != null) ...[
                const SizedBox(height: AppSpacing.lg),
                Container(
                  padding: const EdgeInsets.all(AppSpacing.md),
                  decoration: BoxDecoration(
                    color: AppColors.primaryLight,
                    borderRadius: BorderRadius.circular(16),
                    border: Border.all(color: AppColors.primary.withValues(alpha: 0.3)),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          const Icon(Icons.check_circle, color: AppColors.primary, size: 20),
                          const SizedBox(width: 8),
                          Text('Recipient Verified', style: AppTypography.titleSmall.copyWith(color: AppColors.primaryDark)),
                        ],
                      ),
                      const SizedBox(height: 12),
                      _RecipientRow(label: 'Name', value: _recipientName!),
                      _RecipientRow(label: 'Role', value: AppConfig.roleName(_recipientRole ?? 0)),
                      _RecipientRow(label: 'Location', value: _recipientLocation ?? 'Unknown'),
                    ],
                  ),
                )
                    .animate()
                    .fadeIn(duration: 500.ms)
                    .slideY(begin: 0.1, end: 0, duration: 500.ms),

                const SizedBox(height: AppSpacing.lg),

                // Confirm transfer
                SizedBox(
                  width: double.infinity,
                  height: 52,
                  child: Container(
                    decoration: BoxDecoration(
                      gradient: _isTransferring ? null : AppGradients.primary,
                      borderRadius: BorderRadius.circular(14),
                      boxShadow: _isTransferring
                          ? null
                          : [
                              BoxShadow(
                                color: AppColors.primary.withValues(alpha: 0.3),
                                blurRadius: 12,
                                offset: const Offset(0, 4),
                              ),
                            ],
                    ),
                    child: ElevatedButton.icon(
                      onPressed: _isTransferring ? null : _executeTransfer,
                      icon: _isTransferring
                          ? const SizedBox(
                              width: 18,
                              height: 18,
                              child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                            )
                          : const Icon(Icons.send_rounded),
                      label: Text(_isTransferring
                          ? 'Transferring on blockchain...'
                          : 'Confirm Transfer (${widget.medicineIds.length} medicines)'),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: Colors.transparent,
                        shadowColor: Colors.transparent,
                        disabledBackgroundColor: AppColors.border,
                      ),
                    ),
                  ),
                )
                    .animate()
                    .fadeIn(duration: 500.ms, delay: 200.ms),
              ],
            ],

            if (_transferComplete) ...[
              const SizedBox(height: AppSpacing.lg),
              SizedBox(
                width: double.infinity,
                height: 50,
                child: OutlinedButton.icon(
                  onPressed: () => Navigator.of(context).pop(),
                  icon: const Icon(Icons.arrow_back),
                  label: const Text('Back to Batch'),
                ),
              )
                  .animate()
                  .fadeIn(duration: 500.ms, delay: 300.ms),
            ],

            const SizedBox(height: AppSpacing.xxl),
          ],
        ),
      ),
    );
  }
}

class _RecipientRow extends StatelessWidget {
  final String label;
  final String value;

  const _RecipientRow({required this.label, required this.value});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 3),
      child: Row(
        children: [
          SizedBox(
            width: 70,
            child: Text(label, style: AppTypography.bodySmall.copyWith(color: AppColors.primaryDark)),
          ),
          Expanded(
            child: Text(value, style: AppTypography.bodyMedium.copyWith(color: AppColors.textPrimary)),
          ),
        ],
      ),
    );
  }
}
