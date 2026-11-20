/// Separation of phone-owned navigation, Maps handoff, and simulated events.
enum RouteSource { simulation, hereSdk }

class RouteSignal {
  const RouteSignal({required this.kind, required this.source, required this.simulated});
  final String kind;
  final RouteSource source;
  final bool simulated;
}

class NavigationUnavailable implements Exception {
  const NavigationUnavailable(this.reason);
  final String reason;
  @override
  String toString() => reason;
}

abstract class NavigationProvider {
  Future<void> startRoute({required String journeyId, required bool osLocationPermissionGranted});
  Stream<RouteSignal> subscribe(String journeyId);
  Future<void> stopRoute(String journeyId);
}

class SimulatedRouteProvider implements NavigationProvider {
  SimulatedRouteProvider(this.events);
  final List<String> events;
  bool _active = false;

  @override
  Future<void> startRoute({required String journeyId, required bool osLocationPermissionGranted}) async {
    _active = true;
  }

  @override
  Stream<RouteSignal> subscribe(String journeyId) async* {
    if (!_active) throw const NavigationUnavailable('Demo route not active');
    for (final event in events) {
      if (!_active) return;
      yield RouteSignal(kind: event, source: RouteSource.simulation, simulated: true);
    }
  }

  @override
  Future<void> stopRoute(String journeyId) async { _active = false; }
}

class HereNavigateAdapter implements NavigationProvider {
  const HereNavigateAdapter({this.enabled = false});
  final bool enabled;
  @override
  Future<void> startRoute({required String journeyId, required bool osLocationPermissionGranted}) async {
    if (!enabled) throw const NavigationUnavailable('HERE Navigate feature flag is disabled');
    if (!osLocationPermissionGranted) {
      throw const NavigationUnavailable('Location permission denied');
    }
    throw const NavigationUnavailable('Licensed HERE SDK not integrated');
  }
  @override
  Stream<RouteSignal> subscribe(String journeyId) =>
      Stream<RouteSignal>.error(const NavigationUnavailable('HERE SDK unavailable'));
  @override
  Future<void> stopRoute(String journeyId) async {}
}

class ExternalMapsHandoffAdapter implements NavigationProvider {
  const ExternalMapsHandoffAdapter();
  @override
  Future<void> startRoute({required String journeyId, required bool osLocationPermissionGranted}) async {
    throw const NavigationUnavailable('Use external Maps link, not owned route session');
  }
  @override
  Stream<RouteSignal> subscribe(String journeyId) =>
      Stream<RouteSignal>.error(const NavigationUnavailable('External Maps exposes no live route events'));
  @override
  Future<void> stopRoute(String journeyId) async {}
}
