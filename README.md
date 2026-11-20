# OPTILEXIS — Mobile MVP

> **One journey. Every language.**

This repository contains a walking-first, cross-platform Flutter concept and an authenticated FastAPI journey service. **Sprint 02 introduces durable multi-user storage, token verification and typed integration contracts.** This is a pilot foundation, not a shipped mobile app or connected navigation service.

## Shipped source functionality

- **FastAPI:** authenticated owner-scoped create/read/list/close/delete journeys, persistent consent update, removal of one's own data, capability disclosures.
- **Database:** SQLAlchemy PostgreSQL-compatible model + Alembic revision; SQLite is used for local deterministic migration/testing. Identity, journey sessions, route-mode metadata, recommendation-event metadata and audit metadata are durable.
- **Authentication:** configurable RS256 OIDC access-token validation with issuer, audience and scope checks. A separate local development-token path works only with `ENV=development` and explicit opt-in; **never** ship it to a public service.
- **Journey intelligence:** rule-based simulated airport, station, hotel, parking, off-route event handling and driving distraction suppression. Events are visibly labeled simulated.
- **Flutter:** typed API responses, create/list/inspect/close owner journeys, resume saved trips, Google Maps handoff, debug identity screen, multilingual curated phrasebook and navy/teal design.
- **Provider boundaries:** interfaces for owned vs external navigation, HERE licensing and future ASR/translation/TTS; no provider has been falsely simulated as a live SDK.

## Run the backend locally

Requires Python 3.11+ and a local controlled environment.

```bash
python3 -m pip install -r services/journey-api/requirements-dev.txt
python3 scripts/create_dev_config.py  # generate .env.local and a random development token
./scripts/run_api.sh                 # runs Alembic upgrade and localhost API
```

Visit `http://127.0.0.1:8000/docs`. Keep `.env.local` private and do not expose this debug backend to the public internet. The generated token should be entered in the **debug mobile sign-in screen**.

## Run Flutter locally

Requires Flutter 3.27+ (Dart >= 3.6) and an Android emulator or iOS simulator with native tooling.

```bash
./scripts/bootstrap_flutter.sh  # generates missing Android/iOS project runners
cd apps/mobile
flutter run --dart-define=OPTILEXIS_API_URL=http://10.0.2.2:8000
# iOS simulator: instead use http://127.0.0.1:8000
```

The Flutter app does not include production OAuth login yet. You can authenticate against the development service by pasting the one-time generated **developer token** into the debug-only identity screen. The token is held in memory and not saved to local storage. `https://` is required for remote and non-debug app builds. A production OIDC Authorization Code + PKCE client is a separate integration to implement with the selected provider and secure native token storage.

## Verify

```bash
cd services/journey-api
python -m pytest
# With Flutter toolchain available:
cd ../../apps/mobile
flutter analyze
flutter test
```

The CI workflows independently run backend tests and Flutter lint/widget tests. **Physical mobile builds, live PostgreSQL and real OIDC IdP integration have not been verified in the authoring environment.** Check GitHub Actions before marking the sprint production-ready.

## Data security and isolation

Every journey API operation enforces bearer auth, scope and server-resolved owner. User A cannot read, mutate, close or delete User B's journeys. Only simulation metadata is stored—no raw GPS traces, speech recordings, transcripts, video, or cloud AI prompts. Users can revoke consent and request owned journey or account-data deletion. Retention sweep implementation exists but requires an operator-approved scheduler to run it.

## Intentionally not connected

- No live GPS route tracking, HERE Navigate licensed SDK, external Maps turn events, Meta Wearables, Vantrue streaming, ASR/MT/TTS, CarPlay, Android Auto or LLM-based recommendations.
- No real production identity provider registration, iOS/Android store release, hardened deployment, completed privacy review or active fleet integration.
- The optional 4K camera is **not** a dependency of the phone-first MVP. The published Vantrue OSS disclosure is **not** proof of an authorized camera SDK.

## Repository layout

```text
apps/mobile/                 Flutter app, debug identity screen, typed APIs, provider contracts
services/journey-api/       FastAPI app, SQLAlchemy + Alembic, scoped APIs, unit tests
.github/workflows/          Backend and Flutter verification
scripts/                    Flutter bootstrap, local dev token/config, API runner
docs/AUTH_AND_MIGRATIONS.md Multiuser data/security and migration instructions
docs/IMPLEMENTATION_MATRIX.md Feature coverage and open gaps
codex/SPRINT_02.md          Original Sprint 02 acceptance checklist
AGENTS.md                   Coding-agent rules and scope protection
```

See the architecture/requirements in `docs/PRODUCT_REQUIREMENTS.md` and `docs/ARCHITECTURE.md` for original scope; `docs/Optilexis_Mobile_App_Technical_Architecture_and_Development_Plan.docx` is an associated planning document, not yet included as a binary in GitHub.
