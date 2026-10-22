import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:provider/provider.dart';
import 'package:intl/intl.dart';
import '../../models/batch_model.dart';
import '../../services/blockchain_service.dart';
import '../../services/pinata_service.dart';
import '../../services/private_key_wallet_service.dart';
import '../../services/supabase_service.dart';
import '../../theme/app_theme.dart';
import '../../widgets/page_route.dart';
import '../batch/create_batch_screen.dart';
import '../batch/batch_detail_screen.dart';

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({super.key});

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  List<BatchModel> _batches = [];
  bool _isLoading = true;
  String? _errorMessage;
  bool _showIncomplete = true;
  double _refreshTurns = 0;

  @override
  void initState() {
    super.initState();
    _loadBatches();
  }

  Future<void> _loadBatches() async {
    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    try {
      final walletService = context.read<PrivateKeyWalletService>();
      final blockchainService = context.read<BlockchainService>();
      final pinataService = context.read<PinataService>();

      if (walletService.address == null) {
        throw Exception('Wallet not connected');
      }

      final batchIds = await blockchainService.getManufacturerBatches(
        walletService.address!,
      );

      final batches = <BatchModel>[];
      for (final batchId in batchIds) {
        try {
          final batch = await blockchainService.getBatch(batchId);
          if (batch != null) {
            if (batch.ipfsHash.isNotEmpty) {
              try {
                final ipfsData = await pinataService.fetchFromIPFS(batch.ipfsHash);
                final fullBatch = BatchModel.fromJson(ipfsData);
                batches.add(fullBatch.copyWith(
                  registeredUnits: batch.registeredUnits,
                  isComplete: batch.isComplete,
                  ipfsHash: batch.ipfsHash,
                ));
              } catch (e) {
                batches.add(batch);
              }
            } else {
              batches.add(batch);
            }
          }
        } catch (e) {
          debugPrint('Error loading batch $batchId: $e');
        }
      }

      batches.sort((a, b) => b.createdAt.compareTo(a.createdAt));

      setState(() {
        _batches = batches;
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _errorMessage = 'Failed to load batches: ${e.toString()}';
        _isLoading = false;
      });
    }
  }

  Future<void> _logout() async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
        title: const Text('Logout'),
        content: const Text('Are you sure you want to logout?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Cancel'),
          ),
          TextButton(
            onPressed: () => Navigator.pop(context, true),
            style: TextButton.styleFrom(foregroundColor: AppColors.error),
            child: const Text('Logout'),
          ),
        ],
      ),
    );

    if (confirmed == true) {
      final walletService = context.read<PrivateKeyWalletService>();
      final supabaseService = context.read<SupabaseService>();
      await walletService.logout();
      supabaseService.clear();

      if (mounted) {
        Navigator.of(context).pushReplacementNamed('/');
      }
    }
  }

  int get _totalBatches => _batches.length;
  int get _completedBatches => _batches.where((b) => b.isComplete).length;
  int get _inProgressBatches => _batches.where((b) => !b.isComplete && b.registeredUnits > 0).length;
  int get _totalStrips => _batches.fold(0, (sum, b) => sum + b.totalUnits);

  List<BatchModel> _getFilteredBatches() {
    if (_showIncomplete) return _batches;
    return _batches.where((batch) => batch.isComplete || batch.registeredUnits > 0).toList();
  }

  @override
  Widget build(BuildContext context) {
    final walletService = context.watch<PrivateKeyWalletService>();
    final supabaseService = context.watch<SupabaseService>();
    final address = walletService.address ?? '';
    final shortAddress = address.length >= 42
        ? '${address.substring(0, 6)}...${address.substring(38)}'
        : address;
    final manufacturerName = supabaseService.manufacturer?.name ?? '';

    return Scaffold(
      appBar: AppBar(
        title: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(manufacturerName.isNotEmpty ? manufacturerName : 'Dashboard',
                style: AppTypography.titleLarge),
            Text(shortAddress, style: AppTypography.mono.copyWith(fontSize: 12)),
          ],
        ),
        toolbarHeight: 64,
        actions: [
          PopupMenuButton<String>(
            icon: Icon(Icons.filter_list, color: AppColors.textSecondary),
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
            onSelected: (value) {
              setState(() {
                _showIncomplete = value == 'all';
              });
            },
            itemBuilder: (context) => [
              PopupMenuItem(
                value: 'all',
                child: Row(
                  children: [
                    Icon(_showIncomplete ? Icons.check : null, size: 18, color: AppColors.primary),
                    const SizedBox(width: 8),
                    const Text('Show All Batches'),
                  ],
                ),
              ),
              PopupMenuItem(
                value: 'complete',
                child: Row(
                  children: [
                    Icon(!_showIncomplete ? Icons.check : null, size: 18, color: AppColors.primary),
                    const SizedBox(width: 8),
                    const Text('Hide Incomplete'),
                  ],
                ),
              ),
            ],
          ),
          AnimatedRotation(
            turns: _refreshTurns,
            duration: const Duration(milliseconds: 500),
            curve: Curves.easeInOut,
            child: IconButton(
              icon: Icon(Icons.refresh, color: AppColors.textSecondary),
              onPressed: () {
                setState(() => _refreshTurns += 1);
                _loadBatches();
              },
            ),
          ),
          IconButton(
            icon: Icon(Icons.logout, color: AppColors.textSecondary),
            onPressed: _logout,
          ),
        ],
      ),
      body: RefreshIndicator(
        color: AppColors.primary,
        onRefresh: _loadBatches,
        child: _isLoading
            ? _buildShimmerLoading()
            : _errorMessage != null
                ? _buildErrorState()
                : _batches.isEmpty
                    ? _buildEmptyState()
                    : _buildContent(),
      ),
      floatingActionButton: Container(
        decoration: BoxDecoration(
          gradient: AppGradients.primary,
          borderRadius: BorderRadius.circular(16),
          boxShadow: [
            BoxShadow(
              color: AppColors.primary.withValues(alpha: 0.3),
              blurRadius: 12,
              offset: const Offset(0, 4),
            ),
          ],
        ),
        child: FloatingActionButton.extended(
          onPressed: () {
            HapticFeedback.lightImpact();
            Navigator.push(
              context,
              FadeSlideRoute(page: const CreateBatchScreen()),
            ).then((_) => _loadBatches());
          },
          backgroundColor: Colors.transparent,
          elevation: 0,
          icon: const Icon(Icons.add),
          label: const Text('New Batch'),
        ),
      ).animate().fadeIn(duration: 600.ms, delay: 800.ms).scaleXY(begin: 0.8, end: 1.0, duration: 600.ms, delay: 800.ms, curve: Curves.easeOutBack),
    );
  }

  // ── Shimmer Loading ─────────────────────────────────────────────────────
  Widget _buildShimmerLoading() {
    return ListView(
      padding: const EdgeInsets.fromLTRB(AppSpacing.md, AppSpacing.sm, AppSpacing.md, 100),
      children: [
        // Shimmer stats row
        Padding(
          padding: const EdgeInsets.only(bottom: AppSpacing.md),
          child: Row(
            children: List.generate(4, (i) {
              return Expanded(
                child: Container(
                  margin: EdgeInsets.only(left: i > 0 ? AppSpacing.sm : 0),
                  height: 90,
                  decoration: BoxDecoration(
                    color: AppColors.border.withValues(alpha: 0.3),
                    borderRadius: BorderRadius.circular(16),
                  ),
                )
                    .animate(onPlay: (c) => c.repeat())
                    .shimmer(duration: 1200.ms, color: AppColors.surface.withValues(alpha: 0.5)),
              );
            }),
          ),
        ),
        // Shimmer batch cards
        ...List.generate(3, (i) {
          return Container(
            margin: const EdgeInsets.only(bottom: AppSpacing.sm),
            height: 140,
            decoration: BoxDecoration(
              color: AppColors.border.withValues(alpha: 0.3),
              borderRadius: BorderRadius.circular(20),
            ),
          )
              .animate(onPlay: (c) => c.repeat())
              .shimmer(duration: 1200.ms, delay: Duration(milliseconds: i * 100), color: AppColors.surface.withValues(alpha: 0.5));
        }),
      ],
    );
  }

  // ── Error State ──────────────────────────────────────────────────────────
  Widget _buildErrorState() {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(AppSpacing.lg),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(
              width: 72,
              height: 72,
              decoration: BoxDecoration(
                color: AppColors.error.withValues(alpha: 0.1),
                shape: BoxShape.circle,
              ),
              child: const Icon(Icons.error_outline, size: 36, color: AppColors.error),
            ),
            const SizedBox(height: AppSpacing.md),
            Text(
              _errorMessage!,
              textAlign: TextAlign.center,
              style: AppTypography.bodyMedium,
            ),
            const SizedBox(height: AppSpacing.md),
            ElevatedButton(
              onPressed: _loadBatches,
              child: const Text('Retry'),
            ),
          ],
        )
            .animate()
            .fadeIn(duration: 500.ms)
            .scaleXY(begin: 0.9, end: 1.0, duration: 500.ms, curve: Curves.easeOutCubic),
      ),
    );
  }

  // ── Empty State ──────────────────────────────────────────────────────────
  Widget _buildEmptyState() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Container(
            width: 80,
            height: 80,
            decoration: BoxDecoration(
              color: AppColors.primaryLight,
              shape: BoxShape.circle,
            ),
            child: Icon(Icons.inventory_2_outlined, size: 40, color: AppColors.primary),
          )
              .animate(onPlay: (c) => c.repeat(reverse: true))
              .scaleXY(begin: 1.0, end: 1.06, duration: 2000.ms, curve: Curves.easeInOut),
          const SizedBox(height: AppSpacing.lg),
          Text('No batches yet', style: AppTypography.titleLarge),
          const SizedBox(height: AppSpacing.xs),
          Text(
            'Create your first batch to get started',
            style: AppTypography.bodyMedium,
          ),
        ],
      )
          .animate()
          .fadeIn(duration: 600.ms)
          .slideY(begin: 0.2, end: 0, duration: 600.ms, curve: Curves.easeOutCubic),
    );
  }

  // ── Content ──────────────────────────────────────────────────────────────
  Widget _buildContent() {
    final filtered = _getFilteredBatches();

    return ListView.builder(
      padding: const EdgeInsets.fromLTRB(AppSpacing.md, AppSpacing.sm, AppSpacing.md, 100),
      itemCount: filtered.length + 2,
      itemBuilder: (context, index) {
        if (index == 0) return _buildStatsRow();
        if (index == 1) return _buildSectionHeader();
        return _buildBatchCard(filtered[index - 2], index - 2);
      },
    );
  }

  // ── Stats Row ────────────────────────────────────────────────────────────
  Widget _buildStatsRow() {
    return Padding(
      padding: const EdgeInsets.only(bottom: AppSpacing.md),
      child: Row(
        children: [
          _buildStatCard('Total', _totalBatches, Icons.inventory_2_outlined, [const Color(0xFF10B981), const Color(0xFF059669)], 0),
          const SizedBox(width: AppSpacing.sm),
          _buildStatCard('Complete', _completedBatches, Icons.check_circle_outline, [const Color(0xFF60A5FA), const Color(0xFF3B82F6)], 1),
          const SizedBox(width: AppSpacing.sm),
          _buildStatCard('Active', _inProgressBatches, Icons.pending_outlined, [const Color(0xFFFBBF24), const Color(0xFFF59E0B)], 2),
          const SizedBox(width: AppSpacing.sm),
          _buildStatCard('Strips', _totalStrips, Icons.qr_code_2, [const Color(0xFFA78BFA), const Color(0xFF8B5CF6)], 3),
        ],
      ),
    );
  }

  Widget _buildStatCard(String label, int value, IconData icon, List<Color> colors, int index) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 14, horizontal: 10),
        decoration: BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
            colors: [colors[0].withValues(alpha: 0.1), colors[1].withValues(alpha: 0.05)],
          ),
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: colors[0].withValues(alpha: 0.2)),
        ),
        child: Column(
          children: [
            Icon(icon, size: 20, color: colors[0]),
            const SizedBox(height: AppSpacing.xs),
            TweenAnimationBuilder<int>(
              tween: IntTween(begin: 0, end: value),
              duration: const Duration(milliseconds: 1200),
              curve: Curves.easeOutCubic,
              builder: (context, val, _) {
                return Text(
                  '$val',
                  style: AppTypography.titleMedium.copyWith(fontSize: 18, color: colors[0]),
                );
              },
            ),
            const SizedBox(height: 2),
            Text(label, style: AppTypography.bodySmall),
          ],
        ),
      )
          .animate()
          .fadeIn(duration: 500.ms, delay: Duration(milliseconds: 100 + index * 80))
          .slideY(begin: 0.3, end: 0, duration: 500.ms, delay: Duration(milliseconds: 100 + index * 80), curve: Curves.easeOutCubic),
    );
  }

  Widget _buildSectionHeader() {
    return Padding(
      padding: const EdgeInsets.only(bottom: AppSpacing.sm, top: AppSpacing.xs),
      child: Text('Recent Batches', style: AppTypography.titleMedium),
    ).animate().fadeIn(duration: 400.ms, delay: 500.ms);
  }

  // ── Batch Card ───────────────────────────────────────────────────────────
  Widget _buildBatchCard(BatchModel batch, int index) {
    final dateFormat = DateFormat('MMM dd, yyyy');

    return Padding(
      padding: const EdgeInsets.only(bottom: AppSpacing.sm),
      child: Hero(
        tag: 'batch-${batch.batchId}',
        child: Material(
          color: Colors.transparent,
          child: InkWell(
            borderRadius: BorderRadius.circular(20),
            onTap: () {
              HapticFeedback.lightImpact();
              Navigator.push(
                context,
                FadeSlideRoute(
                  page: BatchDetailScreen(batch: batch),
                ),
              ).then((_) => _loadBatches());
            },
            child: Container(
              padding: const EdgeInsets.all(AppSpacing.md),
              decoration: AppDecorations.elevatedCard,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Header row
                  Row(
                    children: [
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              batch.medicineName.isNotEmpty
                                  ? batch.medicineName
                                  : 'Batch ${batch.batchNumber}',
                              style: AppTypography.titleMedium,
                            ),
                            const SizedBox(height: 2),
                            Text(
                              'Batch #${batch.batchNumber}',
                              style: AppTypography.bodySmall,
                            ),
                          ],
                        ),
                      ),
                      _buildStatusChip(batch),
                      const SizedBox(width: AppSpacing.xs),
                      Icon(Icons.chevron_right, color: AppColors.textTertiary, size: 20),
                    ],
                  ),

                  const SizedBox(height: AppSpacing.md),

                  // Progress
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text('Registration', style: AppTypography.bodySmall),
                      Text(
                        '${batch.registeredUnits}/${batch.totalUnits}',
                        style: AppTypography.labelLarge.copyWith(fontSize: 13),
                      ),
                    ],
                  ),
                  const SizedBox(height: AppSpacing.xs),
                  ClipRRect(
                    borderRadius: BorderRadius.circular(4),
                    child: TweenAnimationBuilder<double>(
                      tween: Tween(begin: 0, end: batch.completionPercentage / 100),
                      duration: const Duration(milliseconds: 1000),
                      curve: Curves.easeOutCubic,
                      builder: (context, value, _) {
                        return LinearProgressIndicator(
                          value: value,
                          backgroundColor: AppColors.border,
                          color: AppColors.primary,
                          minHeight: 6,
                        );
                      },
                    ),
                  ),

                  const SizedBox(height: AppSpacing.md),

                  // Date row
                  Row(
                    children: [
                      Icon(Icons.calendar_today_outlined, size: 14, color: AppColors.textTertiary),
                      const SizedBox(width: AppSpacing.xs),
                      Text(dateFormat.format(batch.createdAt), style: AppTypography.bodySmall),
                      const Spacer(),
                      Icon(Icons.event_outlined, size: 14, color: AppColors.textTertiary),
                      const SizedBox(width: AppSpacing.xs),
                      Text('Exp ${dateFormat.format(batch.expiryDate)}', style: AppTypography.bodySmall),
                    ],
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    )
        .animate()
        .fadeIn(duration: 500.ms, delay: Duration(milliseconds: 600 + index * 80))
        .slideX(begin: 0.15, end: 0, duration: 500.ms, delay: Duration(milliseconds: 600 + index * 80), curve: Curves.easeOutCubic);
  }

  Widget _buildStatusChip(BatchModel batch) {
    final List<Color> colors;
    final String label;

    if (batch.isComplete) {
      colors = [const Color(0xFF10B981), const Color(0xFF059669)];
      label = 'Complete';
    } else if (batch.registeredUnits > 0) {
      colors = [const Color(0xFFFBBF24), const Color(0xFFF59E0B)];
      label = 'In Progress';
    } else {
      colors = [const Color(0xFF60A5FA), const Color(0xFF3B82F6)];
      label = 'New';
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        gradient: LinearGradient(colors: [colors[0].withValues(alpha: 0.15), colors[1].withValues(alpha: 0.08)]),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: colors[0].withValues(alpha: 0.3)),
      ),
      child: Text(
        label,
        style: TextStyle(
          color: colors[1],
          fontWeight: FontWeight.w600,
          fontSize: 12,
          fontFamily: 'Inter',
        ),
      ),
    );
  }
}
