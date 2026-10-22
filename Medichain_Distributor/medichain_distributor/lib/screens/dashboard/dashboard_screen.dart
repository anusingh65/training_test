import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:provider/provider.dart';
import '../../services/private_key_wallet_service.dart';
import '../../services/blockchain_service.dart';
import '../../services/scanner_service.dart';
import '../../services/supabase_service.dart';
import '../../services/cache_service.dart';
import '../../theme/app_theme.dart';
import '../../widgets/page_route.dart';
import '../scanner/qr_scanner_screen.dart';
import '../history/history_screen.dart';
import '../auth/login_screen.dart';

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({super.key});

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  int _myScans = 0;
  int _totalScans = 0;
  int _totalAlerts = 0;
  int _reputationScore = 500;
  List<int> _recentBatchIds = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadDashboardData();
  }

  Future<void> _loadDashboardData() async {
    setState(() => _isLoading = true);

    try {
      final walletService = context.read<PrivateKeyWalletService>();
      final scannerService = context.read<ScannerService>();
      final blockchainService = context.read<BlockchainService>();
      final cacheService = context.read<CacheService>();

      final address = walletService.address!;

      final results = await Future.wait([
        scannerService.getMyTotalScans(address),
        scannerService.getStats(),
        blockchainService.getActorInfo(address),
        cacheService.getRecentScans(),
      ]);

      if (mounted) {
        setState(() {
          _myScans = results[0] as int;
          final stats = results[1] as Map<String, int>;
          _totalScans = stats['totalScans'] ?? 0;
          _totalAlerts = stats['totalAlerts'] ?? 0;
          final actorInfo = results[2] as Map<String, dynamic>?;
          _reputationScore = actorInfo?['reputationScore'] ?? 500;
          _recentBatchIds = results[3] as List<int>;
          _isLoading = false;
        });
      }
    } catch (e) {
      if (mounted) setState(() => _isLoading = false);
      debugPrint('Load dashboard error: $e');
    }
  }

  Future<void> _logout() async {
    final walletService = context.read<PrivateKeyWalletService>();
    await walletService.logout();
    if (mounted) {
      Navigator.of(context).pushReplacement(
        FadeSlideRoute(page: const LoginScreen()),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final supabaseService = context.watch<SupabaseService>();
    final walletService = context.watch<PrivateKeyWalletService>();
    final distributor = supabaseService.distributor;

    return Scaffold(
      backgroundColor: AppColors.background,
      body: RefreshIndicator(
        onRefresh: _loadDashboardData,
        color: AppColors.primary,
        child: CustomScrollView(
          slivers: [
            // App Bar
            SliverAppBar(
              expandedHeight: 200,
              floating: false,
              pinned: true,
              backgroundColor: AppColors.primary,
              flexibleSpace: FlexibleSpaceBar(
                background: Container(
                  decoration: const BoxDecoration(gradient: AppGradients.primary),
                  child: SafeArea(
                    child: Padding(
                      padding: const EdgeInsets.all(AppSpacing.lg),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        mainAxisAlignment: MainAxisAlignment.end,
                        children: [
                          Row(
                            children: [
                              Container(
                                width: 48,
                                height: 48,
                                decoration: BoxDecoration(
                                  color: Colors.white.withValues(alpha: 0.2),
                                  borderRadius: BorderRadius.circular(14),
                                ),
                                child: const Icon(Icons.local_shipping, color: Colors.white, size: 24),
                              ),
                              const SizedBox(width: 12),
                              Expanded(
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text(
                                      distributor?.name ?? 'Distributor',
                                      style: AppTypography.titleMedium.copyWith(color: Colors.white),
                                      maxLines: 1,
                                      overflow: TextOverflow.ellipsis,
                                    ),
                                    Text(
                                      distributor?.license ?? '',
                                      style: AppTypography.bodySmall.copyWith(
                                        color: Colors.white.withValues(alpha: 0.8),
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                              IconButton(
                                icon: const Icon(Icons.logout_rounded, color: Colors.white),
                                onPressed: _logout,
                              ),
                            ],
                          ),
                          const SizedBox(height: 8),
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                            decoration: BoxDecoration(
                              color: Colors.white.withValues(alpha: 0.15),
                              borderRadius: BorderRadius.circular(8),
                            ),
                            child: Text(
                              '${walletService.address?.substring(0, 6)}...${walletService.address?.substring(walletService.address!.length - 4)}',
                              style: AppTypography.mono.copyWith(color: Colors.white, fontSize: 11),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                ),
              ),
              actions: [
                IconButton(
                  icon: const Icon(Icons.refresh_rounded, color: Colors.white),
                  onPressed: _loadDashboardData,
                ),
              ],
            ),

            // Stats Cards
            SliverPadding(
              padding: const EdgeInsets.all(AppSpacing.md),
              sliver: SliverToBoxAdapter(
                child: _isLoading
                    ? const Center(child: Padding(
                        padding: EdgeInsets.all(32),
                        child: CircularProgressIndicator(color: AppColors.primary),
                      ))
                    : Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          // Stats Row
                          Row(
                            children: [
                              Expanded(
                                child: _StatCard(
                                  icon: Icons.qr_code_scanner_rounded,
                                  label: 'My Scans',
                                  value: _myScans.toString(),
                                  colors: [AppColors.primaryGradientStart, AppColors.primaryGradientEnd],
                                ),
                              ),
                              const SizedBox(width: 12),
                              Expanded(
                                child: _StatCard(
                                  icon: Icons.star_rounded,
                                  label: 'Reputation',
                                  value: _reputationScore.toString(),
                                  colors: const [Color(0xFF60A5FA), Color(0xFF3B82F6)],
                                ),
                              ),
                            ],
                          )
                              .animate()
                              .fadeIn(duration: 500.ms, delay: 100.ms)
                              .slideY(begin: 0.1, end: 0, duration: 500.ms, delay: 100.ms),

                          const SizedBox(height: 12),

                          Row(
                            children: [
                              Expanded(
                                child: _StatCard(
                                  icon: Icons.document_scanner_outlined,
                                  label: 'Network Scans',
                                  value: _totalScans.toString(),
                                  colors: const [Color(0xFFFBBF24), Color(0xFFF59E0B)],
                                ),
                              ),
                              const SizedBox(width: 12),
                              Expanded(
                                child: _StatCard(
                                  icon: Icons.warning_amber_rounded,
                                  label: 'Alerts',
                                  value: _totalAlerts.toString(),
                                  colors: const [Color(0xFFEF4444), Color(0xFFDC2626)],
                                ),
                              ),
                            ],
                          )
                              .animate()
                              .fadeIn(duration: 500.ms, delay: 200.ms)
                              .slideY(begin: 0.1, end: 0, duration: 500.ms, delay: 200.ms),

                          const SizedBox(height: AppSpacing.lg),

                          // Quick Actions
                          Text('Quick Actions', style: AppTypography.titleMedium)
                              .animate()
                              .fadeIn(duration: 500.ms, delay: 300.ms),
                          const SizedBox(height: 12),

                          Row(
                            children: [
                              Expanded(
                                child: _ActionCard(
                                  icon: Icons.qr_code_scanner_rounded,
                                  label: 'Scan QR',
                                  subtitle: 'Scan batch code',
                                  onTap: () {
                                    HapticFeedback.lightImpact();
                                    Navigator.of(context).push(
                                      FadeSlideRoute(page: const QRScannerScreen()),
                                    );
                                  },
                                ),
                              ),
                              const SizedBox(width: 12),
                              Expanded(
                                child: _ActionCard(
                                  icon: Icons.history_rounded,
                                  label: 'History',
                                  subtitle: 'View transactions',
                                  onTap: () {
                                    HapticFeedback.lightImpact();
                                    Navigator.of(context).push(
                                      FadeSlideRoute(page: const HistoryScreen()),
                                    );
                                  },
                                ),
                              ),
                            ],
                          )
                              .animate()
                              .fadeIn(duration: 500.ms, delay: 400.ms)
                              .slideY(begin: 0.1, end: 0, duration: 500.ms, delay: 400.ms),

                          const SizedBox(height: AppSpacing.lg),

                          // Distributor Info Card
                          if (distributor != null) ...[
                            Text('Profile', style: AppTypography.titleMedium)
                                .animate()
                                .fadeIn(duration: 500.ms, delay: 500.ms),
                            const SizedBox(height: 12),
                            Container(
                              padding: const EdgeInsets.all(AppSpacing.md),
                              decoration: AppDecorations.card,
                              child: Column(
                                children: [
                                  _InfoRow(icon: Icons.business, label: 'Company', value: distributor.name),
                                  _InfoRow(icon: Icons.badge, label: 'License', value: distributor.license),
                                  _InfoRow(icon: Icons.location_on, label: 'Location', value: distributor.location),
                                  _InfoRow(icon: Icons.person, label: 'Owner', value: distributor.ownerName),
                                  _InfoRow(icon: Icons.phone, label: 'Mobile', value: distributor.mobileNo),
                                ],
                              ),
                            )
                                .animate()
                                .fadeIn(duration: 500.ms, delay: 600.ms)
                                .slideY(begin: 0.1, end: 0, duration: 500.ms, delay: 600.ms),
                          ],

                          const SizedBox(height: AppSpacing.lg),

                          // Recent Scans
                          if (_recentBatchIds.isNotEmpty) ...[
                            Text('Recent Scans', style: AppTypography.titleMedium)
                                .animate()
                                .fadeIn(duration: 500.ms, delay: 700.ms),
                            const SizedBox(height: 12),
                            ...List.generate(
                              _recentBatchIds.length > 5 ? 5 : _recentBatchIds.length,
                              (i) => Container(
                                margin: const EdgeInsets.only(bottom: 8),
                                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                                decoration: AppDecorations.cardSubtle,
                                child: Row(
                                  children: [
                                    Container(
                                      width: 36,
                                      height: 36,
                                      decoration: BoxDecoration(
                                        color: AppColors.primaryLight,
                                        borderRadius: BorderRadius.circular(10),
                                      ),
                                      child: const Icon(Icons.inventory_2_outlined, size: 18, color: AppColors.primary),
                                    ),
                                    const SizedBox(width: 12),
                                    Expanded(
                                      child: Text(
                                        'Batch #${_recentBatchIds[i]}',
                                        style: AppTypography.titleSmall,
                                      ),
                                    ),
                                    const Icon(Icons.chevron_right, color: AppColors.textTertiary, size: 20),
                                  ],
                                ),
                              )
                                  .animate()
                                  .fadeIn(duration: 400.ms, delay: Duration(milliseconds: 800 + i * 80))
                                  .slideX(begin: 0.05, end: 0, duration: 400.ms),
                            ),
                          ],

                          const SizedBox(height: AppSpacing.xxl),
                        ],
                      ),
              ),
            ),
          ],
        ),
      ),

      // FAB - Scan QR
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () {
          HapticFeedback.mediumImpact();
          Navigator.of(context).push(
            FadeSlideRoute(page: const QRScannerScreen()),
          );
        },
        backgroundColor: AppColors.primary,
        icon: const Icon(Icons.qr_code_scanner_rounded),
        label: const Text('Scan'),
      )
          .animate()
          .fadeIn(duration: 600.ms, delay: 800.ms)
          .scaleXY(begin: 0.8, end: 1.0, duration: 600.ms, delay: 800.ms, curve: Curves.easeOutBack),
    );
  }
}

class _StatCard extends StatelessWidget {
  final IconData icon;
  final String label;
  final String value;
  final List<Color> colors;

  const _StatCard({
    required this.icon,
    required this.label,
    required this.value,
    required this.colors,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: AppDecorations.gradientCard(colors),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, color: Colors.white.withValues(alpha: 0.9), size: 22),
          const SizedBox(height: 12),
          Text(value, style: AppTypography.displayMedium.copyWith(color: Colors.white)),
          const SizedBox(height: 2),
          Text(label, style: AppTypography.bodySmall.copyWith(color: Colors.white.withValues(alpha: 0.8))),
        ],
      ),
    );
  }
}

class _ActionCard extends StatelessWidget {
  final IconData icon;
  final String label;
  final String subtitle;
  final VoidCallback onTap;

  const _ActionCard({
    required this.icon,
    required this.label,
    required this.subtitle,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: AppDecorations.card,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Container(
              width: 40,
              height: 40,
              decoration: BoxDecoration(
                color: AppColors.primaryLight,
                borderRadius: BorderRadius.circular(12),
              ),
              child: Icon(icon, color: AppColors.primary, size: 20),
            ),
            const SizedBox(height: 12),
            Text(label, style: AppTypography.titleSmall),
            const SizedBox(height: 2),
            Text(subtitle, style: AppTypography.bodySmall),
          ],
        ),
      ),
    );
  }
}

class _InfoRow extends StatelessWidget {
  final IconData icon;
  final String label;
  final String value;

  const _InfoRow({required this.icon, required this.label, required this.value});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Row(
        children: [
          Icon(icon, size: 16, color: AppColors.textTertiary),
          const SizedBox(width: 10),
          SizedBox(
            width: 70,
            child: Text(label, style: AppTypography.bodySmall),
          ),
          Expanded(
            child: Text(value, style: AppTypography.bodyMedium.copyWith(color: AppColors.textPrimary)),
          ),
        ],
      ),
    );
  }
}
