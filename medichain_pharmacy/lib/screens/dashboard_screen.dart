import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:provider/provider.dart';
import '../services/wallet_service.dart';
import '../services/inventory_service.dart';
import '../theme/app_theme.dart';
import '../widgets/stat_card.dart';
import 'scan_receive_screen.dart';
import 'inventory_screen.dart';
import 'sale_history_screen.dart';
import 'sell_medicine_screen.dart';
import 'login_screen.dart';

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({super.key});

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  int _selectedIndex = 0;

  void _switchToTab(int index) {
    setState(() => _selectedIndex = index);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: IndexedStack(
        index: _selectedIndex,
        children: [
          _HomeTab(onSwitchTab: _switchToTab),
          const InventoryScreen(),
          const SaleHistoryScreen(),
        ],
      ),
      bottomNavigationBar: NavigationBar(
        selectedIndex: _selectedIndex,
        onDestinationSelected: _switchToTab,
        backgroundColor: AppColors.surface,
        indicatorColor: AppColors.primaryLight,
        destinations: const [
          NavigationDestination(
            icon: Icon(Icons.dashboard_outlined),
            selectedIcon: Icon(Icons.dashboard),
            label: 'Home',
          ),
          NavigationDestination(
            icon: Icon(Icons.inventory_2_outlined),
            selectedIcon: Icon(Icons.inventory_2),
            label: 'Inventory',
          ),
          NavigationDestination(
            icon: Icon(Icons.receipt_long_outlined),
            selectedIcon: Icon(Icons.receipt_long),
            label: 'Sales',
          ),
        ],
      ),
    );
  }
}

// ── Home Tab ────────────────────────────────────────────────────────────────

class _HomeTab extends StatelessWidget {
  final ValueChanged<int> onSwitchTab;

  const _HomeTab({required this.onSwitchTab});

  @override
  Widget build(BuildContext context) {
    final wallet = context.watch<WalletService>();
    final inv = context.watch<InventoryService>();

    final shortAddr = wallet.address != null && wallet.address!.length > 12
        ? '${wallet.address!.substring(0, 6)}...${wallet.address!.substring(wallet.address!.length - 4)}'
        : wallet.address ?? '';

    return SafeArea(
      child: CustomScrollView(
        slivers: [
          // App bar
          SliverToBoxAdapter(
            child: Padding(
              padding: const EdgeInsets.fromLTRB(
                  AppSpacing.lg, AppSpacing.lg, AppSpacing.lg, 0),
              child: Row(
                children: [
                  Container(
                    width: 44,
                    height: 44,
                    decoration: BoxDecoration(
                      gradient: AppGradients.primary,
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: const Icon(Icons.storefront_outlined,
                        color: Colors.white, size: 22),
                  ),
                  const SizedBox(width: AppSpacing.md),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text('Pharmacy Portal',
                            style: AppTypography.titleMedium),
                        Text(shortAddr, style: AppTypography.mono),
                      ],
                    ),
                  ),
                  IconButton(
                    onPressed: () => _logout(context),
                    icon: const Icon(Icons.logout, color: AppColors.error),
                    tooltip: 'Logout',
                  ),
                ],
              )
                  .animate()
                  .fadeIn(duration: 500.ms)
                  .slideY(begin: -0.2, end: 0, duration: 500.ms),
            ),
          ),

          // Stats
          SliverToBoxAdapter(
            child: Padding(
              padding: const EdgeInsets.all(AppSpacing.lg),
              child: Row(
                children: [
                  Expanded(
                    child: StatCard(
                      label: 'In Stock',
                      value: inv.availableCount.toString(),
                      icon: Icons.inventory_2_outlined,
                      gradientColors: const [
                        Color(0xFF6366F1),
                        Color(0xFF4F46E5)
                      ],
                    ),
                  ),
                  const SizedBox(width: AppSpacing.md),
                  Expanded(
                    child: StatCard(
                      label: 'Sold',
                      value: inv.dispensedCount.toString(),
                      icon: Icons.shopping_bag_outlined,
                      gradientColors: const [
                        Color(0xFF10B981),
                        Color(0xFF059669)
                      ],
                    ),
                  ),
                  const SizedBox(width: AppSpacing.md),
                  Expanded(
                    child: StatCard(
                      label: 'Total Sales',
                      value: inv.totalSales.toString(),
                      icon: Icons.receipt_long_outlined,
                      gradientColors: const [
                        Color(0xFFF59E0B),
                        Color(0xFFD97706)
                      ],
                    ),
                  ),
                ],
              )
                  .animate()
                  .fadeIn(duration: 500.ms, delay: 200.ms)
                  .slideY(
                      begin: 0.15,
                      end: 0,
                      duration: 500.ms,
                      delay: 200.ms),
            ),
          ),

          // Quick Actions
          SliverToBoxAdapter(
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: AppSpacing.lg),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('Quick Actions', style: AppTypography.titleLarge),
                  const SizedBox(height: AppSpacing.md),

                  _ActionTile(
                    icon: Icons.qr_code_scanner,
                    iconBg: const Color(0xFF6366F1),
                    title: 'Receive Medicine',
                    subtitle: 'Scan QR to add to inventory',
                    onTap: () => Navigator.push(
                      context,
                      MaterialPageRoute(
                          builder: (_) => const ScanReceiveScreen()),
                    ),
                  ),
                  const SizedBox(height: AppSpacing.md),

                  _ActionTile(
                    icon: Icons.sell_outlined,
                    iconBg: const Color(0xFF059669),
                    title: 'Sell Medicine',
                    subtitle: 'Transfer ownership to customer',
                    onTap: () => Navigator.push(
                      context,
                      MaterialPageRoute(
                          builder: (_) => const SellMedicineScreen()),
                    ),
                  ),
                  const SizedBox(height: AppSpacing.md),

                  _ActionTile(
                    icon: Icons.inventory_2_outlined,
                    iconBg: const Color(0xFF3B82F6),
                    title: 'View Inventory',
                    subtitle: '${inv.availableCount} items in stock',
                    onTap: () => onSwitchTab(1),
                  ),
                ],
              )
                  .animate()
                  .fadeIn(duration: 500.ms, delay: 400.ms)
                  .slideY(
                      begin: 0.1,
                      end: 0,
                      duration: 500.ms,
                      delay: 400.ms),
            ),
          ),

          // Recent Sales
          SliverToBoxAdapter(
            child: Padding(
              padding: const EdgeInsets.all(AppSpacing.lg),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text('Recent Sales', style: AppTypography.titleLarge),
                      if (inv.sales.isNotEmpty)
                        TextButton(
                          onPressed: () => onSwitchTab(2),
                          child: const Text('View All'),
                        ),
                    ],
                  ),
                  const SizedBox(height: AppSpacing.sm),
                  if (inv.sales.isEmpty)
                    Container(
                      width: double.infinity,
                      padding: const EdgeInsets.all(AppSpacing.xl),
                      decoration: AppDecorations.card,
                      child: Column(
                        children: [
                          Icon(Icons.receipt_long_outlined,
                              size: 48, color: AppColors.textTertiary),
                          const SizedBox(height: AppSpacing.sm),
                          Text('No sales yet',
                              style: AppTypography.bodyMedium),
                          Text(
                            'Sales will appear here after you sell a medicine',
                            style: AppTypography.bodySmall,
                            textAlign: TextAlign.center,
                          ),
                        ],
                      ),
                    )
                  else
                    ...inv.sales.take(5).map(
                          (sale) => Container(
                            margin:
                                const EdgeInsets.only(bottom: AppSpacing.sm),
                            padding: const EdgeInsets.all(AppSpacing.md),
                            decoration: AppDecorations.card,
                            child: Row(
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
                                        'To: ${sale.shortCustomer}',
                                        style: AppTypography.mono,
                                      ),
                                    ],
                                  ),
                                ),
                                Text(
                                  _timeAgo(sale.timestamp),
                                  style: AppTypography.bodySmall,
                                ),
                              ],
                            ),
                          ),
                        ),
                ],
              )
                  .animate()
                  .fadeIn(duration: 500.ms, delay: 600.ms),
            ),
          ),

          const SliverToBoxAdapter(child: SizedBox(height: AppSpacing.xxl)),
        ],
      ),
    );
  }

  String _timeAgo(DateTime dt) {
    final diff = DateTime.now().difference(dt);
    if (diff.inMinutes < 1) return 'Just now';
    if (diff.inMinutes < 60) return '${diff.inMinutes}m ago';
    if (diff.inHours < 24) return '${diff.inHours}h ago';
    return '${diff.inDays}d ago';
  }

  Future<void> _logout(BuildContext context) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Logout'),
        content: const Text('Are you sure you want to logout?'),
        actions: [
          TextButton(
              onPressed: () => Navigator.pop(ctx, false),
              child: const Text('Cancel')),
          TextButton(
            onPressed: () => Navigator.pop(ctx, true),
            child: const Text('Logout',
                style: TextStyle(color: AppColors.error)),
          ),
        ],
      ),
    );

    if (confirmed == true && context.mounted) {
      final wallet = context.read<WalletService>();
      final inventory = context.read<InventoryService>();
      await inventory.clear();
      await wallet.logout();
      if (context.mounted) {
        Navigator.of(context).pushAndRemoveUntil(
          MaterialPageRoute(builder: (_) => const LoginScreen()),
          (_) => false,
        );
      }
    }
  }
}

// ── Action Tile ─────────────────────────────────────────────────────────────

class _ActionTile extends StatelessWidget {
  final IconData icon;
  final Color iconBg;
  final String title;
  final String subtitle;
  final VoidCallback onTap;

  const _ActionTile({
    required this.icon,
    required this.iconBg,
    required this.title,
    required this.subtitle,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Material(
      color: Colors.transparent,
      child: InkWell(
        borderRadius: BorderRadius.circular(16),
        onTap: () {
          HapticFeedback.lightImpact();
          onTap();
        },
        child: Container(
          padding: const EdgeInsets.all(AppSpacing.md),
          decoration: AppDecorations.card,
          child: Row(
            children: [
              Container(
                width: 48,
                height: 48,
                decoration: BoxDecoration(
                  color: iconBg.withValues(alpha: 0.1),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Icon(icon, color: iconBg, size: 24),
              ),
              const SizedBox(width: AppSpacing.md),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(title, style: AppTypography.titleSmall),
                    Text(subtitle, style: AppTypography.bodySmall),
                  ],
                ),
              ),
              const Icon(Icons.chevron_right, color: AppColors.textTertiary),
            ],
          ),
        ),
      ),
    );
  }
}
