import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:flutter/foundation.dart';
import 'models.dart';

/// Implement this with OIDC Authorization Code + PKCE and secure token storage
/// when an actual identity provider is provisioned. No production OIDC client
/// credentials or tokens are embedded in this app.
abstract class AccessTokenProvider {
  Future<String?> accessToken();
}

class UnconfiguredAccessTokenProvider implements AccessTokenProvider {
  const UnconfiguredAccessTokenProvider();
  @override
  Future<String?> accessToken() async => null;
}

/// Debug-only identity for local simulator. The token is held in memory.
/// Never place a real OIDC token or a development token in a release build.
class DebugAccessTokenProvider implements AccessTokenProvider {
  String? _token;
  DebugAccessTokenProvider() {
    if (kDebugMode) {
      const configured = String.fromEnvironment('OPTILEXIS_DEV_TOKEN');
      if (configured.isNotEmpty) _token = configured;
    }
  }
  bool get configured => _token?.isNotEmpty == true;
  void setToken(String value) {
    if (!kDebugMode) throw StateError('Debug token sign-in is unavailable in release mode');
    _token = value.trim().isEmpty ? null : value.trim();
  }
  void clear() => _token = null;
  @override
  Future<String?> accessToken() async => kDebugMode ? _token : null;
}

class OptilexisApi {
  OptilexisApi({String? baseUrl, AccessTokenProvider? tokenProvider})
      : _baseUrl = baseUrl ?? const String.fromEnvironment(
            'OPTILEXIS_API_URL', defaultValue: 'http://10.0.2.2:8000'),
        _tokenProvider = tokenProvider ?? DebugAccessTokenProvider();

  final String _baseUrl;
  final AccessTokenProvider _tokenProvider;
  final HttpClient _client = HttpClient()..connectionTimeout = const Duration(seconds: 8);

  String get baseUrl => _baseUrl;
  bool get canEnterDebugToken => kDebugMode && _tokenProvider is DebugAccessTokenProvider;
  bool get debugTokenConfigured => _tokenProvider is DebugAccessTokenProvider &&
      _tokenProvider.configured;

  void setDebugToken(String token) {
    if (!canEnterDebugToken) throw const OptilexisApiException('Development sign-in unavailable');
    _tokenProvider.setToken(token);
  }
  void clearDebugToken() {
    if (_tokenProvider is DebugAccessTokenProvider) {
      _tokenProvider.clear();
    }
  }

  Future<Map<String, dynamic>> health() => _object('GET', '/health', requiresAuth: false);
  Future<Map<String, dynamic>> capabilities() => _object('GET', '/v1/capabilities', requiresAuth: false);

  Future<JourneyDto> createJourney({
    required String destination,
    required String language,
    required String mode,
    required String navigationMode,
    required bool consentLocation,
    required bool consentMicrophone,
  }) async => JourneyDto.fromJson(await _object('POST', '/v1/journeys', body: {
    'destination': destination,
    'language': language,
    'mode': mode,
    'navigation_mode': navigationMode,
    'consent': {
      'location': consentLocation,
      'microphone': consentMicrophone,
      'camera': false,
    },
  }));

  Future<List<JourneyDto>> listJourneys() async {
    final response = await _request('GET', '/v1/journeys');
    if (response is! List) throw const OptilexisApiException('Invalid journey list response');
    return response.map((value) => JourneyDto.fromJson(value as Map<String, dynamic>)).toList();
  }

  Future<JourneyDto> getJourney(String id) async =>
      JourneyDto.fromJson(await _object('GET', '/v1/journeys/${Uri.encodeComponent(id)}'));

  Future<EventOutcomeDto> sendSimulationEvent({
    required String journeyId,
    required String event,
    required bool parked,
  }) async => EventOutcomeDto.fromJson(await _object(
    'POST', '/v1/journeys/${Uri.encodeComponent(journeyId)}/events', body: {
      'event': event,
      'source': 'simulation',
      'parked': parked,
    },
  ));

  Future<PhraseDto> demoPhrase({required String phraseKey, required String language}) async =>
      PhraseDto.fromJson(await _object('POST', '/v1/translation/demo-phrase', body: {
        'phrase_key': phraseKey,
        'language': language,
      }));

  Future<JourneyDto> closeJourney(String id) async =>
      JourneyDto.fromJson(await _object('POST', '/v1/journeys/${Uri.encodeComponent(id)}/close', body: {}));

  Future<Map<String, dynamic>> _object(String method, String path, {
    Map<String, dynamic>? body, bool requiresAuth = true,
  }) async {
    final response = await _request(method, path, body: body, requiresAuth: requiresAuth);
    if (response is! Map<String, dynamic>) {
      throw const OptilexisApiException('Unexpected response from API');
    }
    return response;
  }

  Future<Object?> _request(String method, String path, {
    Map<String, dynamic>? body, bool requiresAuth = true,
  }) async {
    try {
      final base = Uri.parse(_baseUrl);
      const localHosts = <String>{'localhost', '127.0.0.1', '10.0.2.2'};
      if (base.scheme != 'https' && (!kDebugMode || !localHosts.contains(base.host))) {
        throw const OptilexisApiException('HTTPS required except debug loopback/emulator');
      }
      final uri = base.resolve(path);
      final token = requiresAuth ? await _tokenProvider.accessToken() : null;
      if (requiresAuth && (token == null || token.isEmpty)) {
        throw const OptilexisApiException('Sign in required: development token or approved OIDC identity');
      }
      final req = await _client.openUrl(method, uri).timeout(const Duration(seconds: 10));
      req.headers.contentType = ContentType.json;
      req.headers.set(HttpHeaders.acceptHeader, 'application/json');
      if (token != null) req.headers.set(HttpHeaders.authorizationHeader, 'Bearer $token');
      if (body != null) req.write(jsonEncode(body));
      final resp = await req.close().timeout(const Duration(seconds: 10));
      final raw = await resp.transform(utf8.decoder).join();
      final decoded = raw.isEmpty ? null : jsonDecode(raw);
      if (resp.statusCode >= 400) {
        final detail = decoded is Map ? decoded['detail'] : raw;
        throw OptilexisApiException('HTTP ${resp.statusCode}: $detail');
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
    } on TimeoutException {
      throw const OptilexisApiException('Request timed out; check backend connection');
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
