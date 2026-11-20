# Codex task brief — Sprint 02

## Objective

Move Optilexis from a locally simulated single-user app to a properly isolated, testable **multi-user pilot foundation**, without adding live hardware integrations prematurely.

## Workstream A: Authentication and persistence

- Add PostgreSQL + Alembic models for users, sessions, consents, routes, recommendation events and audit metadata.
- Add OIDC identity integration through a configurable provider; enforce scopes and record ownership on every journey endpoint.
- Preserve local developer mode only behind an explicit `ENV=development` setting, never silently as fallback.
- Replace in-memory storage with repository interface and test isolation/authorization.
- Add explicit retention and deletion interfaces; include safe migration and rollback path.

## Workstream B: Navigation contracts

- Define `NavigationProvider` (start route, subscribe to location and maneuver events, stop route, handle permission denial).
- Keep `Google/Apple Maps handoff` distinct from `Optilexis-guided mode`.
- Implement a deterministic simulated provider for test/demo mode; add a typed feature-flagged HERE Navigate adapter boundary.
- Do not embed HERE commercial artifacts or credentials; document the separate licensed SDK setup.

## Workstream C: Translation contracts

- Add `SpeechTranslator` interface (ASR, translation, TTS). Keep the existing curated phrasebook as a demo provider.
- Add authorization, cost/timeout constraints and consent hooks in provider interface.
- No automatic microphone capture before an explicit user action and OS-level permission.
- Instrument response latency and errors without storing raw content by default.

## Workstream D: Flutter quality

- Bootstrap Android/iOS runners with the script, then run `flutter analyze` and `flutter test`.
- Introduce typed API models, error states, testable providers and widget tests.
- Implement account/sign-in screen only after server identity flow exists.
- Keep Optilexis brand colors and an accessible, audio-first UX. Existing screens must remain functional.

## Acceptance

1. Authenticated User A cannot read, list, update or close User B's journeys (403/404, no data leaks).
2. Journey data survives backend restart with a real database.
3. Android/iOS app can start, inspect and close a user-owned trip on a development backend.
4. Navigation simulation clearly identifies simulated events and cannot impersonate a real SDK event.
5. Driving safety suppression passes all new test scenarios.
6. `flutter analyze`, Flutter tests and backend tests pass; no sensitive keys in source.
7. `docs/IMPLEMENTATION_MATRIX.md` updated to report only verified functionality.

## Later milestones (separate approvals)

- HERE Navigate real route progress and map SDK: requires license/credentials and on-device validation.
- Meta Wearables toolkit physical-hardware audio bridge.
- Streaming speech ASR/MT/TTS, observability and controlled data handling.
- Vantrue camera integration only after a documented authorized SDK and network feasibility study.
- CarPlay/Android Auto native interfaces only after qualification and review.
