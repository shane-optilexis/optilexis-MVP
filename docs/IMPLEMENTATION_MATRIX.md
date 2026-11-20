# Optilexis requirements-to-code traceability

**Sprint 02 status, Nov 2026.** "Verified" means local automated Python tests passed. It does **not** mean the Flutter app compiled, deployed or connected to a hardware SDK.

| Requirement | Implementation | Verification and remaining gap |
|---|---|---|
| Authenticated API | `optilexis_api/auth.py`, `settings.py` | Verified dev bearer and mocked RS256 OIDC validation; live identity provider not provisioned |
| Scoped multiuser journeys | `main.py`, `repository.py` | Verified 401/403/404 and cross-user isolation for read/write/delete/close/event/consent |
| Durable journey storage | SQLAlchemy tables + Alembic `0001` | Verified on migrated SQLite across app restarts; PostgreSQL CI integration test added, result pending |
| Users and sessions | `users`, `journey_sessions` | Persisted; JWT is stateless; production session revocation remains IdP responsibility |
| Consents / audit metadata | `consents`, `audit_events` | Persisted; explicit update, no sensor activation; privacy retention review pending |
| Deletion / retention | `DELETE /v1/me/data`, `DELETE /v1/journeys/{id}`, `purge_closed_journeys` | Verified explicit deletion; background retention schedule pending |
| Context recommendations | `predictor.py`, `recommendation_events` | Verified simulated event rules and metadata; not real navigation |
| Driving safety | `predictor.py` | Verified suppression for moving vehicles; safety review pending |
| Navigation interface | `navigation.py`, `navigation_contract.dart` | Simulation labeled, permission denial & disabled-by-default HERE boundary; licensed HERE SDK unavailable |
| Maps handoff | `main.dart::_handoff` | Source provided, no app-to-app route telemetry; mobile device test pending |
| Translation provider | `translation.py`, `speech_contract.dart` | Provider contract, consent/cost/timeout gate + demo phrasebook; no live ASR/MT/TTS |
| Flutter typed API (`material_ui` 1.x) | `api_client.dart`, `models.dart` | Code implemented, history and debug sign-in wired; `flutter analyze/test` CI pending |
| Seven-language phrasebook | `phrases.py` | Previously verified; limited curated demonstration translations |
| Vantrue E1 Pro S | Architecture only | Official camera video interface unverified; no actual integration |
| Meta glasses | Architecture only | Native device access/bridge not built |
| CarPlay and Android Auto | Architecture only | Qualifying native implementation and review pending |
| OpenAI/LLM assistant | Architecture only | No production reasoning service connected |

**Risk gates:** User route state is not inferred from external Google/Apple Maps; video is never silently uploaded; tokens are not hard-coded; development mode requires explicit configuration and must remain local-only.
