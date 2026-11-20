import 'package:flutter_test/flutter_test.dart';
import 'package:optilexis_mobile/src/oidc_auth.dart';
import 'package:optilexis_mobile/src/phone_location.dart';

void main() {
  test('OIDC requires HTTPS issuer and redirect scheme', () {
    const disabled = OidcConfiguration(issuer: '', clientId: 'app', redirectUri: 'ai.optilexis://auth/callback', scopes: 'openid');
    expect(disabled.isConfigured, false);
    const enabled = OidcConfiguration(issuer: 'https://login.example.org', clientId: 'native-app',
      redirectUri: 'ai.optilexis://auth/callback', scopes: 'openid profile journeys:read');
    expect(enabled.isConfigured, true);
    expect(enabled.requestedScopes, contains('journeys:read'));
  });

  test('location requires explicit consent before invoking native plugin', () async {
    final location = PhoneLocation();
    await expectLater(location.current(userConsent: false, userActivated: true), throwsStateError);
    await expectLater(location.current(userConsent: true, userActivated: false), throwsStateError);
  });
}
