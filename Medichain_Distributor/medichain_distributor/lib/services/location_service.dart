import 'package:flutter/foundation.dart';
import 'package:geolocator/geolocator.dart';
import 'package:geocoding/geocoding.dart';

class LocationService {
  Position? _lastPosition;
  String? _lastAddress;

  Position? get lastPosition => _lastPosition;
  String? get lastAddress => _lastAddress;

  Future<bool> checkAndRequestPermission() async {
    bool serviceEnabled = await Geolocator.isLocationServiceEnabled();
    if (!serviceEnabled) {
      debugPrint('Location services are disabled');
      return false;
    }

    LocationPermission permission = await Geolocator.checkPermission();
    if (permission == LocationPermission.denied) {
      permission = await Geolocator.requestPermission();
      if (permission == LocationPermission.denied) {
        debugPrint('Location permission denied');
        return false;
      }
    }

    if (permission == LocationPermission.deniedForever) {
      debugPrint('Location permission permanently denied');
      return false;
    }

    return true;
  }

  Future<Position?> getCurrentPosition() async {
    try {
      final hasPermission = await checkAndRequestPermission();
      if (!hasPermission) return null;

      _lastPosition = await Geolocator.getCurrentPosition(
        locationSettings: const LocationSettings(
          accuracy: LocationAccuracy.high,
          timeLimit: Duration(seconds: 10),
        ),
      );

      debugPrint('GPS: ${_lastPosition!.latitude}, ${_lastPosition!.longitude}');
      return _lastPosition;
    } catch (e) {
      debugPrint('Get position error: $e');
      return null;
    }
  }

  Future<String> reverseGeocode(double latitude, double longitude) async {
    try {
      final placemarks = await placemarkFromCoordinates(latitude, longitude);
      if (placemarks.isNotEmpty) {
        final p = placemarks.first;
        final parts = <String>[];
        if (p.subLocality?.isNotEmpty == true) parts.add(p.subLocality!);
        if (p.locality?.isNotEmpty == true) parts.add(p.locality!);
        if (p.administrativeArea?.isNotEmpty == true) parts.add(p.administrativeArea!);
        if (p.country?.isNotEmpty == true) parts.add(p.country!);

        _lastAddress = parts.join(', ');
        return _lastAddress!;
      }
      return '$latitude, $longitude';
    } catch (e) {
      debugPrint('Reverse geocode error: $e');
      return '$latitude, $longitude';
    }
  }

  Future<({Position position, String address})?> getLocationWithAddress() async {
    final position = await getCurrentPosition();
    if (position == null) return null;

    final address = await reverseGeocode(position.latitude, position.longitude);
    return (position: position, address: address);
  }
}
