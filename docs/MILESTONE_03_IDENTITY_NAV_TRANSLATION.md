# Milestone 03 — Identity, navigation and translation integration

## 1. Register an actual native OIDC client

Optilexis uses Authorization Code + PKCE through the system browser and Flutter AppAuth. It stores only short-lived API access and optional refresh tokens in native secure storage. The API verifies JWT signatures, audience, issuer, expiry and scopes. This release has NO real identity provider tenant, registered callback or production login test.

Choose and provision an IdP (Auth0, Okta or Entra External ID). Register a NATIVE PUBLIC client with redirect URI: ai.optilexis://auth/callback. Configure API audience and scopes: journeys:read, journeys:write, translation:demo, translation:live. Native clients must NEVER carry a client secret. Providers differ in their custom-scope and audience setup.

Public app configuration:
~~~bash
flutter run --dart-define=OPTILEXIS_API_URL=https://api.example.org --dart-define=OPTILEXIS_OIDC_ISSUER=https://idp.example.org/ --dart-define=OPTILEXIS_OIDC_CLIENT_ID=registered-native-client --dart-define=OPTILEXIS_OIDC_REDIRECT_URI=ai.optilexis://auth/callback --dart-define=OPTILEXIS_OIDC_AUDIENCE=optilexis-api
~~~

Set OPTILEXIS_OIDC_AUDIENCE_PARAMETER=audience ONLY if the provider requires that query parameter (Auth0-style). The backend must use the matching OIDC_ISSUER, OIDC_AUDIENCE and OIDC_JWKS_URL with a migrated PostgreSQL database and development auth disabled.

On physical devices test sign-in, cancellation, expiry, refresh, insufficient scope, revocation, logout, reinstall, network loss and tenant discovery. Local sign-out clears device tokens; it does not terminate browser sessions or revoke remote grants.

## 2. Live typed text translation only

Authenticated endpoint: POST /v1/translation/text. It requires the translation:live scope, an owned active WALKING journey, and an explicit user-activated request. A request is limited to 400 characters and 1000 UTF-8 bytes. Driving mode is disabled irrespective of a client supplied 'parked' flag. No raw text is stored by the app.

Server-only secret configuration:
~~~text
TEXT_TRANSLATOR=azure
AZURE_TRANSLATOR_ENDPOINT=https://<resource>.cognitiveservices.azure.com/translator/text/v3.0/translate
AZURE_TRANSLATOR_REGION=<region>
AZURE_TRANSLATOR_KEY=<server-side-secret>
~~~

HTTP-mock tests cover payloads, errors, ownership and safety. A real Azure Translator subscription was NOT contacted; validate account billing/quotas, regional data rules, rate limiting and privacy before a pilot. Real microphone ASR, speech TTS, duplex dialogue and offline translation are not implemented.

## 3. Navigation and device privacy

The phone offers an on-demand single foreground GPS reading after both app consent and OS permission. The result is not uploaded or retained. This does NOT establish route progress, ETA, traffic or spoken turns. Google/Apple Maps external handoff does not give Optilexis live events. HERE Navigate Flutter is an external licensed SDK requiring its package/credentials and integration of route, positioning, route progress and maneuver listeners.

## 4. Native build CI

The bootstrap script generates Flutter Android/iOS runners and adds native AppAuth callback scheme plus foreground-only location permissions. GitHub checks execute Flutter analysis/tests and separate Android debug APK and unsigned iOS simulator builds. A passing build does NOT verify real phone sign-in, sensor permissions, provisioning, store eligibility or driver-safety field behavior.

## Remaining launch gates

Connect a real OIDC provider; complete real-provider login, token refresh and revocation checks; connect and validate Azure regional endpoint and billing; license HERE Navigate and obtain route events; enforce rate limits, TLS, privacy retention, security monitoring; sign and test on real iOS and Android devices.
