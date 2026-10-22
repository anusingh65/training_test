import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../models/medicine_item.dart';
import '../models/sale_record.dart';

/// Manages local inventory cache and sales history.
/// The source of truth is the blockchain; this caches for offline display.
class InventoryService extends ChangeNotifier {
  List<MedicineItem> _inventory = [];
  List<SaleRecord> _sales = [];
  bool _isLoaded = false;

  List<MedicineItem> get inventory => List.unmodifiable(_inventory);
  List<MedicineItem> get availableInventory =>
      _inventory.where((m) => m.isAtPharmacy).toList();
  List<MedicineItem> get dispensedInventory =>
      _inventory.where((m) => m.isDispensed).toList();
  List<SaleRecord> get sales => List.unmodifiable(_sales);
  bool get isLoaded => _isLoaded;

  int get totalItems => _inventory.length;
  int get availableCount => availableInventory.length;
  int get dispensedCount => dispensedInventory.length;
  int get totalSales => _sales.length;

  /// Load cached data from local storage.
  Future<void> load() async {
    final prefs = await SharedPreferences.getInstance();

    final invJson = prefs.getString('pharmacy_inventory');
    if (invJson != null) {
      final list = jsonDecode(invJson) as List;
      _inventory = list.map((e) => MedicineItem.fromJson(e)).toList();
    }

    final salesJson = prefs.getString('pharmacy_sales');
    if (salesJson != null) {
      _sales = SaleRecord.decodeList(salesJson);
    }

    _isLoaded = true;
    notifyListeners();
  }

  /// Persist current state.
  Future<void> _save() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(
      'pharmacy_inventory',
      jsonEncode(_inventory.map((m) => m.toJson()).toList()),
    );
    await prefs.setString('pharmacy_sales', SaleRecord.encodeList(_sales));
  }

  /// Add a medicine to local inventory (after receiving it on-chain).
  void addMedicine(MedicineItem item) {
    // Avoid duplicates
    _inventory.removeWhere((m) => m.id == item.id);
    _inventory.add(item);
    _save();
    notifyListeners();
  }

  /// Mark a medicine as dispensed and record the sale.
  void recordSale(SaleRecord sale) {
    // Update local status
    final idx = _inventory.indexWhere((m) => m.id == sale.medicineId);
    if (idx != -1) {
      final old = _inventory[idx];
      _inventory[idx] = MedicineItem(
        id: old.id,
        batchId: old.batchId,
        ipfsHash: old.ipfsHash,
        contentHash: old.contentHash,
        currentOwner: sale.customerAddress,
        status: 4, // Dispensed
        batchNumber: old.batchNumber,
        manufacturer: old.manufacturer,
      );
    }

    _sales.insert(0, sale);
    _save();
    notifyListeners();
  }

  /// Refresh a single medicine's on-chain status locally.
  void updateMedicine(MedicineItem updated) {
    final idx = _inventory.indexWhere((m) => m.id == updated.id);
    if (idx != -1) {
      _inventory[idx] = updated;
    } else {
      _inventory.add(updated);
    }
    _save();
    notifyListeners();
  }

  /// Clear all local data (on logout).
  Future<void> clear() async {
    _inventory.clear();
    _sales.clear();
    _isLoaded = false;
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove('pharmacy_inventory');
    await prefs.remove('pharmacy_sales');
    notifyListeners();
  }
}
