import 'dart:io';
import 'dart:typed_data';
import 'dart:ui' as ui;
import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:path_provider/path_provider.dart';
import 'package:pdf/pdf.dart';
import 'package:pdf/widgets.dart' as pw;
import 'package:printing/printing.dart';
import 'package:qr_flutter/qr_flutter.dart';
import '../models/medicine_model.dart';

class QRService {
  // Generate QR code widget
  Widget generateQRWidget({
    required String data,
    double size = 200,
    Color? foregroundColor,
    Color? backgroundColor,
  }) {
    return QrImageView(
      data: data,
      size: size,
      backgroundColor: backgroundColor ?? Colors.white,
      foregroundColor: foregroundColor ?? Colors.black,
      errorCorrectionLevel: QrErrorCorrectLevel.H,
    );
  }

  // Generate QR code as image bytes
  Future<Uint8List> generateQRImageBytes({
    required String data,
    double size = 512,
  }) async {
    final qrValidationResult = QrValidator.validate(
      data: data,
      version: QrVersions.auto,
      errorCorrectionLevel: QrErrorCorrectLevel.H,
    );

    if (qrValidationResult.status != QrValidationStatus.valid) {
      throw Exception('Invalid QR data');
    }

    final qrCode = qrValidationResult.qrCode!;

    final painter = QrPainter.withQr(
      qr: qrCode,
      color: Colors.black,
      emptyColor: Colors.white,
      gapless: true,
    );

    final imageSize = size.toInt();
    final pictureRecorder = ui.PictureRecorder();
    final canvas = Canvas(pictureRecorder);

    painter.paint(canvas, Size(size, size));

    final picture = pictureRecorder.endRecording();
    final image = await picture.toImage(imageSize, imageSize);
    final byteData = await image.toByteData(format: ui.ImageByteFormat.png);

    return byteData!.buffer.asUint8List();
  }

  // Save QR code as PNG file
  Future<String> saveQRCodeAsFile({
    required String data,
    required String filename,
    double size = 512,
  }) async {
    try {
      final imageBytes = await generateQRImageBytes(data: data, size: size);

      final directory = await getApplicationDocumentsDirectory();
      final filePath = '${directory.path}/$filename.png';
      final file = File(filePath);

      await file.writeAsBytes(imageBytes);

      debugPrint('✅ QR code saved: $filePath');
      return filePath;
    } catch (e) {
      debugPrint('❌ Save QR code error: $e');
      rethrow;
    }
  }

  // Generate PDF with multiple QR codes (for batch printing)
  Future<Uint8List> generateBatchQRPDF({
    required List<MedicineModel> medicines,
    required String batchNumber,
    String? batchQRData,
  }) async {
    final pdf = pw.Document();

    // Generate QR code images
    final qrImages = <String, Uint8List>{};

    // Add batch QR if provided
    if (batchQRData != null) {
      qrImages['BATCH'] = await generateQRImageBytes(
        data: batchQRData,
        size: 256,
      );
    }

    // Add medicine QRs (in batches to avoid memory issues)
    for (final medicine in medicines) {
      qrImages[medicine.medicineId.toString()] = await generateQRImageBytes(
        data: medicine.qrData,
        size: 256,
      );
    }

    // Create PDF pages (4 QR codes per page in 2x2 grid)
    final entries = qrImages.entries.toList();
    final totalPages = (entries.length / 4).ceil();

    for (int pageIndex = 0; pageIndex < totalPages; pageIndex++) {
      final startIndex = pageIndex * 4;
      final endIndex = (startIndex + 4).clamp(0, entries.length);
      final pageEntries = entries.sublist(startIndex, endIndex);

      pdf.addPage(
        pw.Page(
          pageFormat: PdfPageFormat.a4,
          build: (context) {
            return pw.Column(
              children: [
                // Header
                pw.Container(
                  padding: const pw.EdgeInsets.all(20),
                  child: pw.Column(
                    crossAxisAlignment: pw.CrossAxisAlignment.start,
                    children: [
                      pw.Text(
                        'MediChain QR Codes',
                        style: pw.TextStyle(
                          fontSize: 24,
                          fontWeight: pw.FontWeight.bold,
                        ),
                      ),
                      pw.SizedBox(height: 8),
                      pw.Text(
                        'Batch: $batchNumber',
                        style: const pw.TextStyle(fontSize: 16),
                      ),
                      pw.Text(
                        'Page ${pageIndex + 1} of $totalPages',
                        style: const pw.TextStyle(fontSize: 12),
                      ),
                    ],
                  ),
                ),

                pw.Divider(),

                // QR Grid (2x2)
                pw.Expanded(
                  child: pw.GridView(
                    crossAxisCount: 2,
                    children: pageEntries.map((entry) {
                      return pw.Container(
                        padding: const pw.EdgeInsets.all(16),
                        child: pw.Column(
                          mainAxisAlignment: pw.MainAxisAlignment.center,
                          children: [
                            pw.Image(
                              pw.MemoryImage(entry.value),
                              width: 200,
                              height: 200,
                            ),
                            pw.SizedBox(height: 8),
                            pw.Text(
                              entry.key == 'BATCH'
                                  ? 'Batch QR'
                                  : 'Strip #${entry.key}',
                              style: pw.TextStyle(
                                fontSize: 14,
                                fontWeight: pw.FontWeight.bold,
                              ),
                            ),
                          ],
                        ),
                      );
                    }).toList(),
                  ),
                ),

                // Footer
                pw.Container(
                  padding: const pw.EdgeInsets.all(16),
                  child: pw.Text(
                    'Generated by MediChain Manufacturer App',
                    style: const pw.TextStyle(fontSize: 10),
                  ),
                ),
              ],
            );
          },
        ),
      );
    }

    return pdf.save();
  }

  // Print QR codes
  Future<void> printQRCodes({
    required List<MedicineModel> medicines,
    required String batchNumber,
    String? batchQRData,
  }) async {
    try {
      final pdfBytes = await generateBatchQRPDF(
        medicines: medicines,
        batchNumber: batchNumber,
        batchQRData: batchQRData,
      );

      await Printing.layoutPdf(
        onLayout: (format) async => pdfBytes,
      );

      debugPrint('✅ QR codes sent to printer');
    } catch (e) {
      debugPrint('❌ Print error: $e');
      rethrow;
    }
  }

  // Share/Save PDF
  Future<void> sharePDF({
    required List<MedicineModel> medicines,
    required String batchNumber,
    String? batchQRData,
  }) async {
    try {
      final pdfBytes = await generateBatchQRPDF(
        medicines: medicines,
        batchNumber: batchNumber,
        batchQRData: batchQRData,
      );

      await Printing.sharePdf(
        bytes: pdfBytes,
        filename: 'batch_${batchNumber}_qr_codes.pdf',
      );

      debugPrint('✅ PDF shared');
    } catch (e) {
      debugPrint('❌ Share PDF error: $e');
      rethrow;
    }
  }

  // Save PDF to file
  Future<String> savePDFToFile({
    required List<MedicineModel> medicines,
    required String batchNumber,
    String? batchQRData,
  }) async {
    try {
      final pdfBytes = await generateBatchQRPDF(
        medicines: medicines,
        batchNumber: batchNumber,
        batchQRData: batchQRData,
      );

      final directory = await getApplicationDocumentsDirectory();
      final filePath = '${directory.path}/batch_${batchNumber}_qr_codes.pdf';
      final file = File(filePath);

      await file.writeAsBytes(pdfBytes);

      debugPrint('✅ PDF saved: $filePath');
      return filePath;
    } catch (e) {
      debugPrint('❌ Save PDF error: $e');
      rethrow;
    }
  }

  // Generate batch QR data with verification info
  String generateBatchQRData({
    required int batchId,
    required String batchNumber,
    required int totalUnits,
  }) {
    return '{"type":"batch","id":$batchId,"number":"$batchNumber","units":$totalUnits,"contract":"0x555d8aFe7FD29eC64D84e930b1Bf0265D1cC68A8","network":"sepolia"}';
  }
}
