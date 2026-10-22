import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:provider/provider.dart';
import '../../config/app_config.dart';
import '../../services/private_key_wallet_service.dart';
import '../../services/blockchain_service.dart';
import '../../services/supabase_service.dart';
import '../../theme/app_theme.dart';
import '../../widgets/page_route.dart';
import '../dashboard/dashboard_screen.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _privateKeyController = TextEditingController();
  bool _isLoading = false;
  bool _obscureKey = true;
  String? _errorMessage;

  @override
  void initState() {
    super.initState();
    _tryAutoLogin();
  }

  @override
  void dispose() {
    _privateKeyController.dispose();
    super.dispose();
  }

  Future<void> _tryAutoLogin() async {
    final walletService = context.read<PrivateKeyWalletService>();
    final success = await walletService.tryAutoLogin();

    if (success && mounted) {
      await _verifyAndNavigate();
    }
  }

  Future<void> _loginWithPrivateKey() async {
    if (_privateKeyController.text.trim().isEmpty) {
      setState(() {
        _errorMessage = 'Please enter your private key';
      });
      return;
    }

    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    try {
      final walletService = context.read<PrivateKeyWalletService>();
      await walletService.loginWithPrivateKey(_privateKeyController.text.trim());

      if (mounted) {
        await _verifyAndNavigate();
      }
    } catch (e) {
      setState(() {
        _errorMessage = 'Login failed: ${e.toString()}';
        _isLoading = false;
      });
    }
  }

  Future<void> _verifyAndNavigate() async {
    try {
      final walletService = context.read<PrivateKeyWalletService>();
      final blockchainService = context.read<BlockchainService>();
      final supabaseService = context.read<SupabaseService>();

      if (!walletService.isConnected || walletService.address == null) {
        throw Exception('Not connected');
      }

      final isManufacturer = await blockchainService.isManufacturer(walletService.address!);

      if (isManufacturer) {
        await supabaseService.fetchManufacturer(walletService.address!);

        if (mounted) {
          Navigator.of(context).pushReplacement(
            FadeSlideRoute(page: const DashboardScreen()),
          );
        }
      } else {
        setState(() {
          _errorMessage = 'Access denied: This address is not registered as a manufacturer.\n'
              'Please contact the admin to register your address.';
          _isLoading = false;
        });

        await walletService.logout();
      }
    } catch (e) {
      setState(() {
        _errorMessage = 'Verification failed: ${e.toString()}';
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Container(
        decoration: const BoxDecoration(
          gradient: AppGradients.background,
        ),
        child: SafeArea(
          child: Center(
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(AppSpacing.lg),
              child: ConstrainedBox(
                constraints: const BoxConstraints(maxWidth: 400),
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    // Logo
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
                      child: const Icon(
                        Icons.local_pharmacy_outlined,
                        size: 40,
                        color: Colors.white,
                      ),
                    )
                        .animate(onPlay: (c) => c.repeat(reverse: true))
                        .scaleXY(
                          begin: 1.0,
                          end: 1.04,
                          duration: 2000.ms,
                          curve: Curves.easeInOut,
                        )
                        .animate() // entrance animation
                        .fadeIn(duration: 600.ms, curve: Curves.easeOut)
                        .scaleXY(begin: 0.5, end: 1.0, duration: 600.ms, curve: Curves.easeOutBack),

                    const SizedBox(height: AppSpacing.lg),

                    // Title
                    Text('MediChain', style: AppTypography.displayLarge)
                        .animate()
                        .fadeIn(duration: 600.ms, delay: 200.ms)
                        .slideY(begin: 0.3, end: 0, duration: 600.ms, delay: 200.ms, curve: Curves.easeOutCubic),

                    const SizedBox(height: AppSpacing.xs),

                    Text(
                      'Manufacturer Portal',
                      style: AppTypography.bodyMedium,
                    ).animate().fadeIn(duration: 600.ms, delay: 400.ms),

                    const SizedBox(height: AppSpacing.xxl),

                    // Form card
                    Container(
                      padding: const EdgeInsets.all(AppSpacing.lg),
                      decoration: AppDecorations.elevatedCard,
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            'Login with Private Key',
                            style: AppTypography.titleLarge,
                          ),
                          const SizedBox(height: AppSpacing.xs),
                          Text(
                            'Enter your Ethereum private key to continue',
                            style: AppTypography.bodyMedium,
                          ),

                          const SizedBox(height: AppSpacing.lg),

                          // Private Key Input
                          TextField(
                            controller: _privateKeyController,
                            obscureText: _obscureKey,
                            decoration: InputDecoration(
                              labelText: 'Private Key',
                              hintText: '0x...',
                              prefixIcon: const Icon(Icons.vpn_key_outlined, size: 20),
                              suffixIcon: IconButton(
                                icon: Icon(
                                  _obscureKey ? Icons.visibility_outlined : Icons.visibility_off_outlined,
                                  size: 20,
                                ),
                                onPressed: () {
                                  setState(() {
                                    _obscureKey = !_obscureKey;
                                  });
                                },
                              ),
                            ),
                            maxLines: _obscureKey ? 1 : 3,
                            enabled: !_isLoading,
                          ),

                          const SizedBox(height: AppSpacing.md),

                          // Warning
                          Container(
                            padding: const EdgeInsets.all(12),
                            decoration: BoxDecoration(
                              color: const Color(0xFFFFFBEB),
                              borderRadius: BorderRadius.circular(12),
                              border: Border.all(color: const Color(0xFFFDE68A)),
                            ),
                            child: Row(
                              children: [
                                Icon(Icons.warning_amber_rounded, color: Colors.amber.shade700, size: 18),
                                const SizedBox(width: AppSpacing.sm),
                                Expanded(
                                  child: Text(
                                    'Never share your private key with anyone',
                                    style: AppTypography.bodySmall.copyWith(
                                      color: Colors.amber.shade900,
                                    ),
                                  ),
                                ),
                              ],
                            ),
                          ),

                          const SizedBox(height: AppSpacing.lg),

                          // Error message
                          if (_errorMessage != null)
                            Container(
                              margin: const EdgeInsets.only(bottom: AppSpacing.md),
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
                                      style: AppTypography.bodySmall.copyWith(
                                        color: AppColors.error,
                                      ),
                                    ),
                                  ),
                                ],
                              ),
                            )
                                .animate()
                                .fadeIn(duration: 300.ms)
                                .slideX(begin: -0.1, end: 0, duration: 300.ms)
                                .shake(hz: 3, duration: 400.ms, delay: 100.ms),

                          // Login Button
                          SizedBox(
                            width: double.infinity,
                            height: 50,
                            child: Container(
                              decoration: BoxDecoration(
                                gradient: _isLoading ? null : AppGradients.primary,
                                borderRadius: BorderRadius.circular(12),
                                boxShadow: _isLoading
                                    ? null
                                    : [
                                        BoxShadow(
                                          color: AppColors.primary.withValues(alpha: 0.3),
                                          blurRadius: 12,
                                          offset: const Offset(0, 4),
                                        ),
                                      ],
                              ),
                              child: ElevatedButton(
                                onPressed: _isLoading ? null : () {
                                  HapticFeedback.lightImpact();
                                  _loginWithPrivateKey();
                                },
                                style: ElevatedButton.styleFrom(
                                  backgroundColor: Colors.transparent,
                                  shadowColor: Colors.transparent,
                                  disabledBackgroundColor: AppColors.border,
                                ),
                                child: _isLoading
                                    ? const SizedBox(
                                        height: 20,
                                        width: 20,
                                        child: CircularProgressIndicator(
                                          strokeWidth: 2,
                                          color: Colors.white,
                                        ),
                                      )
                                    : const Text('Login'),
                              ),
                            ),
                          ),
                        ],
                      ),
                    )
                        .animate()
                        .fadeIn(duration: 600.ms, delay: 600.ms)
                        .slideY(begin: 0.2, end: 0, duration: 600.ms, delay: 600.ms, curve: Curves.easeOutCubic),

                    const SizedBox(height: AppSpacing.lg),

                    // Network Info
                    Text(
                      'Network: ${AppConfig.networkName}',
                      style: AppTypography.bodySmall,
                    ).animate().fadeIn(duration: 600.ms, delay: 1000.ms),

                    const SizedBox(height: AppSpacing.xxl),

                    // Footer
                    Text(
                      'Powered by Blockchain & IPFS',
                      style: AppTypography.bodySmall.copyWith(
                        color: AppColors.textTertiary,
                      ),
                    ).animate().fadeIn(duration: 600.ms, delay: 1200.ms),
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}
