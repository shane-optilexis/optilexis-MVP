import 'dart:convert';
import 'dart:io';

/// Debug-only API; configure with --dart-define=OPTILEXIS_API_URL=...
/// No secrets, tokens or cloud AI keys should be embedded in this mobile app.
class OptilexisApi {
  OptilexisApi({String? baseUrl})
      : _baseUrl = baseUrl ??
            const String.fromEnvironment(
              'OPTILEXIS_API_URL',
              defaultValue: 'http://10.0.2.2:8000',
            );

  final String _baseUrl;
  final HttpClient _client = HttpClient()
    ..connectionTimeout = const Duration(seconds: 8);

  String get baseUrl => _baseUrl;

  Future<Map<String, dynamic>> health() => _request('GET', '/health');
  Future<Map<String, dynamic>> capabilities() =>
      _request('GET', '/v1/capabilities');

  Future<Map<String, dynamic>> createJourney({
    required String destination,
    required String language,
    required String mode,
    required String navigationMode,
    required bool consentLocation,
    required bool consentMicrophone,
  }) =>
      _request('POST', '/v1/journeys', body: {
        'destination': destination,
        'language': language,
        'mode': mode,
        'navigation_mode': navigationMode,
        'consent': {
          'location': consentLocation,
          'microphone': consentMicrophone,
          'camera': false,
        },
      });

  Future<Map<String, dynamic>> sendSimulationEvent({
    required String journeyId,
    required String event,
    required bool parked,
  }) =>
      _request('POST', '/v1/journeys/$journeyId/events', body: {
        'event': event,
        'source': 'simulation',
        'parked': parked,
      });

  Future<Map<String, dynamic>> demoPhrase({
    required String phraseKey,
    required String language,
  }) =>
      _request('POST', '/v1/translation/demo-phrase', body: {
        'phrase_key': phraseKey,
        'language': language,
      });

  Future<Map<String, dynamic>> closeJourney(String journeyId) =>
      _request('POST', '/v1/journeys/$journeyId/close', body: {});

  Future<Map<String, dynamic>> _request(
    String method,
    String path, {
    Map<String, dynamic>? body,
  }) async {
    try {
      final uri = Uri.parse('$_baseUrl$path');
      final req = await _client.openUrl(method, uri).timeout(
        const Duration(seconds: 10),
      );
      req.headers.contentType = ContentType.json;
      req.headers.set(HttpHeaders.acceptHeader, 'application/json');
      if (body != null) req.write(jsonEncode(body));
      final resp = await req.close().timeout(const Duration(seconds: 10));
      final raw = await resp.transform(utf8.decoder).join();
      final decoded = raw.isEmpty ? <String, dynamic>{} : jsonDecode(raw);
      if (resp.statusCode >= 400) {
        final detail = decoded is Map ? decoded['detail'] : raw;
        throw OptilexisApiException('HTTP ${resp.statusCode}: $detail');
      }
      if (decoded is! Map<String, dynamic>) {
        throw const OptilexisApiException('Unexpected response from API');
      }
      return decoded;
    } on OptilexisApiException {
      rethrow;
    } on SocketException {
      throw OptilexisApiException('API unreachable at $_baseUrl');
    } on HandshakeException {
      throw const OptilexisApiException('TLS connection failed');
    } on FormatException {
      throw const OptilexisApiException('Invalid API JSON response');
    }
  }

  void dispose() => _client.close(force: true);
}

class OptilexisApiException implements Exception {
  const OptilexisApiException(this.message);
  final String message;
  @override
  String toString() => message;
}
