import 'package:flutter_test/flutter_test.dart';
import 'package:optilexis_mobile/src/models.dart';
import 'package:optilexis_mobile/src/navigation_contract.dart';
import 'package:optilexis_mobile/src/speech_contract.dart';

void main() {
  test('typed journey response preserves ownership-safe fields', () {
    final dto = JourneyDto.fromJson({
      'id': 'journey-123', 'destination': 'Shinjuku', 'language': 'ja',
      'mode': 'walk', 'navigation_mode': 'maps_handoff', 'stage': 'started',
      'consent': {'location': false, 'microphone': false, 'camera': false},
      'created_at': '2026-11-19T00:00:00Z', 'closed_at': null,
    });
    expect(dto.active, true);
    expect(dto.consent.microphone, false);
    expect(dto.destination, 'Shinjuku');
  });

  test('simulation events are explicitly labeled', () async {
    final route = SimulatedRouteProvider(['station_approach']);
    await route.startRoute(journeyId: 'trip', osLocationPermissionGranted: false);
    final events = await route.subscribe('trip').toList();
    expect(events.single.simulated, true);
    expect(events.single.source, RouteSource.simulation);
  });

  test('HERE route rejects missing OS permission', () async {
    await expectLater(
      const HereNavigateAdapter().startRoute(journeyId: 'trip', osLocationPermissionGranted: false),
      throwsA(isA<NavigationUnavailable>()),
    );
  });

  test('speech rejects capture without all three consent gates', () async {
    final speech = UnconfiguredSpeechProvider();
    await expectLater(
      speech.recognize([], 'ja', const SpeechConsent(
        consentGranted: true, osPermissionGranted: false, userActivated: true)),
      throwsA(isA<SpeechUnavailable>()),
    );
  });
}
