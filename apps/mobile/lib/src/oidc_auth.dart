import 'package:flutter_appauth/flutter_appauth.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

/// OIDC application identifiers are public configuration, never a client secret.
class OidcConfiguration {
  const OidcConfiguration({
    required this.issuer,
    required this.clientId,
    required this.redirectUri,
    required this.scopes,
    this.audience = '',
    this.audienceParameter = '',
  });

  factory OidcConfiguration.fromEnvironment() => const OidcConfiguration(
        issuer: String.fromEnvironment('OPTILEXIS_OIDC_ISSUER'),
        clientId: String.fromEnvironment('OPTILEXIS_OIDC_CLIENT_ID'),
        redirectUri: String.fromEnvironment('OPTILEXIS_OIDC_REDIRECT_URI',
            defaultValue: 'ai.optilexis://auth/callback'),
        scopes: String.fromEnvironment('OPTILEXIS_OIDC_SCOPES',
            defaultValue: 'openid profile offline_access journeys:read journeys:write translation:demo translation:live'),
        audience: String.fromEnvironment('OPTILEXIS_OIDC_AUDIENCE'),
        audienceParameter: String.fromEnvironment('OPTILEXIS_OIDC_AUDIENCE_PARAMETER'),
      );

  final String issuer;
  final String clientId;
  final String redirectUri;
  final String scopes;
  final String audience;
  final String audienceParameter;

  bool get isConfigured => issuer.startsWith('https://') &&
      clientId.trim().isNotEmpty &&
      Uri.tryParse(redirectUri)?.scheme == 'ai.optilexis';

  List<String> get requestedScopes => scopes.split(RegExp(r'\s+')).where((e) => e.isNotEmpty).toList();
  Map<String, String>? get additionalParameters =>
      audience.isNotEmpty && audienceParameter.isNotEmpty
          ? <String, String>{audienceParameter: audience} : null;
}

/// AppAuth owns PKCE, state and nonce; OS-backed storage owns the token cache.
class OidcSession {
  OidcSession(this.config, {FlutterAppAuth? appAuth, FlutterSecureStorage? storage})
      : _appAuth = appAuth ?? const FlutterAppAuth(),
        _storage = storage ?? const FlutterSecureStorage();

  final OidcConfiguration config;
  final FlutterAppAuth _appAuth;
  final FlutterSecureStorage _storage;
  static const _keyAccess = 'optilexis.oidc.access';
  static const _keyRefresh = 'optilexis.oidc.refresh';
  static const _keyExpiry = 'optilexis.oidc.expiry';

  Future<void> signIn() async {
    if (!config.isConfigured) throw StateError('OIDC provider is not configured');
    final response = await _appAuth.authorizeAndExchangeCode(
      AuthorizationTokenRequest(
        config.clientId,
        config.redirectUri,
        issuer: config.issuer,
        scopes: config.requestedScopes,
        additionalParameters: config.additionalParameters,
      ),
    );
    if (response?.accessToken == null) throw StateError('Identity provider returned no API access token');
    await _save(response!.accessToken!, response.refreshToken,
        response.accessTokenExpirationDateTime);
  }

  Future<String?> accessToken() async {
    if (!config.isConfigured) return null;
    final value = await _storage.read(key: _keyAccess);
    if (value == null) return null;
    final expiryRaw = await _storage.read(key: _keyExpiry);
    final expires = expiryRaw == null ? null : DateTime.tryParse(expiryRaw);
    if (expires != null && DateTime.now().toUtc().isBefore(expires.subtract(const Duration(seconds: 60)))) {
      return value;
    }
    final refreshToken = await _storage.read(key: _keyRefresh);
    if (refreshToken == null || refreshToken.isEmpty) {
      await signOut();
      return null;
    }
    try {
      final response = await _appAuth.token(TokenRequest(
        config.clientId,
        config.redirectUri,
        issuer: config.issuer,
        refreshToken: refreshToken,
        scopes: config.requestedScopes,
      ));
      if (response?.accessToken == null) throw StateError('Access token refresh failed');
      await _save(response!.accessToken!, response.refreshToken ?? refreshToken,
          response.accessTokenExpirationDateTime);
      return response.accessToken;
    } catch (_) {
      await signOut();
      rethrow;
    }
  }

  Future<void> _save(String access, String? refresh, DateTime? expiry) async {
    await _storage.write(key: _keyAccess, value: access);
    if (refresh != null) await _storage.write(key: _keyRefresh, value: refresh);
    await _storage.write(key: _keyExpiry, value: expiry?.toUtc().toIso8601String());
  }

  /// Deletes local credentials, not the remote IdP browser session.
  Future<void> signOut() async {
    for (final key in [_keyAccess, _keyRefresh, _keyExpiry]) {
      await _storage.delete(key: key);
    }
  }
