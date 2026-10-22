import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:supabase_flutter/supabase_flutter.dart';
import '../../config/theme.dart';
import '../../widgets/verification_badge.dart';

class HistoryScreen extends StatefulWidget {
  const HistoryScreen({super.key});

  @override
  State<HistoryScreen> createState() => _HistoryScreenState();
}

class _HistoryScreenState extends State<HistoryScreen> {
  List<Map<String, dynamic>> _scans = [];
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _loadHistory();
  }

  Future<void> _loadHistory() async {
    final client = Supabase.instance.client;
    final user = client.auth.currentUser;
    if (user == null) return;

    final data = await client
        .from('verification_scans')
        .select()
        .eq('scanner_id', user.id)
        .order('scanned_at', ascending: false)
        .limit(50);

    if (mounted) {
      setState(() {
        _scans = List<Map<String, dynamic>>.from(data);
        _loading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Scan History')),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _scans.isEmpty
              ? const Center(child: Text('No scans yet', style: TextStyle(color: Colors.grey)))
              : ListView.builder(
                  padding: const EdgeInsets.all(16),
                  itemCount: _scans.length,
                  itemBuilder: (context, index) {
                    final scan = _scans[index];
                    return Card(
                      margin: const EdgeInsets.only(bottom: 12),
                      child: ListTile(
                        onTap: () => context.push('/drug/${scan['drug_id']}'),
                        leading: Icon(
                          scan['result'] == 'verified'
                              ? Icons.check_circle
                              : scan['result'] == 'suspicious'
                                  ? Icons.warning
                                  : Icons.dangerous,
                          color: scan['result'] == 'verified'
                              ? AppColors.verified
                              : scan['result'] == 'suspicious'
                                  ? AppColors.suspicious
                                  : AppColors.counterfeit,
                        ),
                        title: Text(scan['drug_id'] ?? '', style: const TextStyle(fontSize: 14)),
                        subtitle: Text(
                          '${scan['location'] ?? 'Unknown'} • ${DateTime.tryParse(scan['scanned_at'] ?? '')?.toLocal().toString().substring(0, 16) ?? ''}',
                          style: const TextStyle(fontSize: 12, color: Colors.grey),
                        ),
                        trailing: VerificationBadge(status: scan['result'] ?? 'pending'),
                      ),
                    );
                  },
                ),
    );
  }
}
