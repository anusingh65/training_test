import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:mobile_scanner/mobile_scanner.dart';
import '../../config/theme.dart';
import '../../providers/scan_provider.dart';
import '../../providers/drug_provider.dart';

class ScanReceiveScreen extends ConsumerStatefulWidget {
  const ScanReceiveScreen({super.key});

  @override
  ConsumerState<ScanReceiveScreen> createState() => _ScanReceiveScreenState();
}

class _ScanReceiveScreenState extends ConsumerState<ScanReceiveScreen> {
  final MobileScannerController _controller = MobileScannerController();
  bool _processing = false;

  void _onDetect(BarcodeCapture capture) async {
    if (_processing) return;
    final barcode = capture.barcodes.firstOrNull;
    if (barcode?.rawValue == null) return;

    final raw = barcode!.rawValue!;
    final scanService = ref.read(scanServiceProvider);
    final parsed = scanService.parseQrPayload(raw);

    if (parsed == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Invalid QR code')),
      );
      return;
    }

    setState(() => _processing = true);

    // Load drug details
    final drugService = ref.read(drugServiceProvider);
    final drug = await drugService.getDrug(parsed['drugId']!);

    if (!mounted) return;

    if (drug == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Drug not found in database')),
      );
      setState(() => _processing = false);
      return;
    }

    context.push('/commuter/confirm', extra: {
      'drug': drug,
      'qrData': parsed,
    });

    setState(() => _processing = false);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Scan Shipment')),
      body: Stack(
        children: [
          MobileScanner(controller: _controller, onDetect: _onDetect),
          Center(
            child: Container(
              width: 250,
              height: 250,
              decoration: BoxDecoration(
                border: Border.all(color: AppColors.primary, width: 3),
                borderRadius: BorderRadius.circular(20),
              ),
            ),
          ),
          Positioned(
            bottom: 60,
            left: 0,
            right: 0,
            child: Center(
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 10),
                decoration: BoxDecoration(
                  color: Colors.black54,
                  borderRadius: BorderRadius.circular(20),
                ),
                child: Text(
                  _processing ? 'Loading...' : 'Scan batch QR code',
                  style: const TextStyle(color: Colors.white),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }
}
