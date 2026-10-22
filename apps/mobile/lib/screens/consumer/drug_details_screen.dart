import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../config/theme.dart';
import '../../models/drug.dart';
import '../../models/custody_event.dart';
import '../../providers/drug_provider.dart';
import '../../widgets/timeline_widget.dart';
import '../../widgets/verification_badge.dart';

class DrugDetailsScreen extends ConsumerStatefulWidget {
  final String drugId;

  const DrugDetailsScreen({super.key, required this.drugId});

  @override
  ConsumerState<DrugDetailsScreen> createState() => _DrugDetailsScreenState();
}

class _DrugDetailsScreenState extends ConsumerState<DrugDetailsScreen> {
  Drug? _drug;
  List<CustodyEvent> _events = [];
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  Future<void> _loadData() async {
    final drugService = ref.read(drugServiceProvider);
    final drug = await drugService.getDrug(widget.drugId);
    final events = await drugService.getCustodyChain(widget.drugId);

    if (mounted) {
      setState(() {
        _drug = drug;
        _events = events;
        _loading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text(_drug?.name ?? 'Drug Details')),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _drug == null
              ? const Center(child: Text('Drug not found'))
              : SingleChildScrollView(
                  padding: const EdgeInsets.all(20),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Expanded(
                            child: Text(
                              _drug!.name,
                              style: Theme.of(context).textTheme.titleLarge?.copyWith(
                                    fontWeight: FontWeight.bold,
                                  ),
                            ),
                          ),
                          VerificationBadge(status: _drug!.status),
                        ],
                      ),
                      const SizedBox(height: 20),

                      Card(
                        child: Padding(
                          padding: const EdgeInsets.all(16),
                          child: Column(
                            children: [
                              _row('Drug ID', _drug!.drugId),
                              _row('Batch', _drug!.batchId),
                              _row('Manufacturer', _drug!.manufacturer),
                              _row('Mfg Date', _drug!.manufactureDate),
                              _row('Expiry', _drug!.expiryDate),
                              if (_drug!.flagged)
                                _row('Status', 'FLAGGED',
                                    valueColor: AppColors.counterfeit),
                            ],
                          ),
                        ),
                      ),
                      const SizedBox(height: 24),

                      Text(
                        'Supply Chain',
                        style: Theme.of(context).textTheme.titleMedium?.copyWith(
                              fontWeight: FontWeight.w600,
                            ),
                      ),
                      const SizedBox(height: 12),

                      if (_events.isEmpty)
                        const Card(
                          child: Padding(
                            padding: EdgeInsets.all(24),
                            child: Center(
                              child: Text('No custody events', style: TextStyle(color: Colors.grey)),
                            ),
                          ),
                        )
                      else
                        TimelineWidget(events: _events),
                    ],
                  ),
                ),
    );
  }

  Widget _row(String label, String value, {Color? valueColor}) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: const TextStyle(color: Colors.grey, fontSize: 13)),
          Text(value,
              style: TextStyle(fontSize: 13, color: valueColor, fontWeight: FontWeight.w500)),
        ],
      ),
    );
  }
}
