# Optilexis — Mobile MVP / Codex Starter

> **One journey. Every language.**  
> Development starter created from `docs/Optilexis_Mobile_App_Technical_Architecture_and_Development_Plan.docx`.

## What works in this first coding increment

- **Python/FastAPI journey API:** create, inspect, close and simulate journeys.
- **Context-aware rules engine:** airport, station, hotel, parking and off-route recommendations.
- **Driving safety policy:** suppresses nonessential contextual prompts while moving.
- **Seven-language curated phrasebook:** English, Japanese, French, Spanish, German, Chinese and Thai.
- **Flutter mobile UI source:** trip setup, language/mode selections, map handoff, manual scenario tests, results and device status.
- **9 automated backend tests** passing in this build environment.
- **Original Word specification** included in `docs/`.

## Not working yet (must not be represented as operational)

- No HERE Navigate SDK, real location tracking, licensed route calculation or live maneuver events.
- No live ASR, machine translation, TTS, AI LLM or speech streaming. Curated phrases only.
- No physical Meta glasses, Vantrue camera API, video processing or supported in-car UI.
- No production accounts, authorization, durable persistence or privacy/regulatory approval.
- There is no deployed backend, App Store binary, or hosted web app in this archive.
- Flutter cannot be compiled in the authoring environment; use the instructions below to create native runners and validate it on your machine or Codex environment.

## 1. Run the backend

Requires Python 3.11+.

```bash
cd services/journey-api
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
python -m pytest
uvicorn optilexis_api.main:app --host 127.0.0.1 --port 8000 --reload
```

Open `http://127.0.0.1:8000/docs` for interactive API documentation.

**Security:** This backend is a local, unauthenticated, single-user simulator. Do not bind it publicly or deploy to production. For physical devices, first add a properly authenticated and TLS-secured development environment.

## 2. Run the Flutter app

Requires Flutter 3.27+ (Dart 3.6+) and Android Studio / Xcode. In a Flutter-enabled terminal:

```bash
./scripts/bootstrap_flutter.sh
cd apps/mobile
flutter doctor
flutter run --dart-define=OPTILEXIS_API_URL=http://10.0.2.2:8000
```

`10.0.2.2` is the Android emulator's alias for the development machine. On an iOS simulator, use `http://127.0.0.1:8000`. For a physical phone, follow security and networking prerequisites—do **not** expose the unauthenticated API to the public network.

The bootstrap script generates missing native Android/iOS runner files using `flutter create`, adds Android **debug-only** cleartext HTTP allowance, obtains packages, analyzes Dart and runs Flutter tests. The non-generated source files already exist under `apps/mobile/lib`.

Google Maps handoff opens an external directions link but does **not** provide route progress back to Optilexis. Choosing `own_route` shows that SDK integration remains pending.

## 3. Example end-to-end API flow

```bash
# Start a trip.
curl -s http://127.0.0.1:8000/v1/journeys \
  -H 'Content-Type: application/json' \
  -d '{"destination":"Shinjuku Station, Tokyo","language":"ja","mode":"walk"}'

# Copy the returned id and simulate a route-context event.
curl -s http://127.0.0.1:8000/v1/journeys/YOUR_JOURNEY_ID/events \
  -H 'Content-Type: application/json' \
  -d '{"event":"station_approach","source":"simulation"}'

# Obtain a curated phrase (not a live translation).
curl -s http://127.0.0.1:8000/v1/translation/demo-phrase \
  -H 'Content-Type: application/json' \
  -d '{"phrase_key":"station_platform","language":"ja"}'
```

## 4. Handoff to Codex

1. Unzip the repository and open the folder as a Codex project or push it to a connected GitHub repository.
2. Read `AGENTS.md`, `docs/IMPLEMENTATION_MATRIX.md`, and the original Word requirements.
3. Start with `codex/SPRINT_02.md`; complete its acceptance tests before expanding scope.
4. Commit each feature increment and keep unverified hardware integrations behind adapters.

**Suggested first Codex instruction:**

> Read `AGENTS.md` and the attached requirements in `docs/`. Run the FastAPI tests, then bootstrap and analyze the Flutter mobile app. Fix build issues without claiming unimplemented integrations. Implement Sprint 02 (authenticated, persistent journey storage and testable navigation provider interfaces). Include tests and a brief verification report.

## Repository map

```text
apps/mobile/               Flutter client source (requires flutter create runners)
services/journey-api/      FastAPI backend, prediction rules and test suite
codex/SPRINT_02.md         Next coding iteration and acceptance tests
AGENTS.md                  Codex working rules and scope protections
docs/IMPLEMENTATION_MATRIX.md
  ↳ Feature implementation coverage, verified/pending status
docs/Optilexis_Mobile_App_Technical_Architecture_and_Development_Plan.docx
  ↳ Original product/architecture requirement
.github/workflows/         Backend test automation
```

## External references

- HERE Flutter Navigation: https://docs.here.com/here-sdk/docs/flutter-navigation
- HERE Flutter SDK integration: https://docs.here.com/here-sdk/docs/flutter-integrate-here-sdk
- Flutter url_launcher: https://pub.dev/packages/url_launcher
- Vantrue E1 Pro S: https://www.vantrue.com/products/element-1-pro-s-4k-dashcam
- Vantrue source disclosure: https://www.vantrue.com/pages/open-source-software

No commercial integration rights are inferred from published product marketing or OSS disclosures.
