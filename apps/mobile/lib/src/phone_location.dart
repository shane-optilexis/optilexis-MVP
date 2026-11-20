import 'package:geolocator/geolocator.dart';

/// One-shot, opt-in foreground location only. No route or maneuver inference.
class PhoneLocation {
  Future<Position> current({required bool userConsent, required bool userActivated}) async {
    if (!userConsent || !userActivated) {
      throw StateError('Location needs explicit consent and a user action');
    }
    if (!await Geolocator.isLocationServiceEnabled()) {
      throw StateError('Enable location services on your device');
    }
    var permission = await Geolocator.checkPermission();
    if (permission == LocationPermission.denied) {
      permission = await Geolocator.requestPermission();
    }
    if (permission == LocationPermission.denied ||
        permission == LocationPermission.deniedForever) {
      throw StateError('Device location permission denied');
    }
    return Geolocator.getCurrentPosition(
      locationSettings: const LocationSettings(
        accuracy: LocationAccuracy.medium,
        timeLimit: Duration(seconds: 10),
      ),
    );
  }
}
