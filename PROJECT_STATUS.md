# Optilexis engineering status — Sprint 02

Implemented locally and proposed for `sprint-02-auth-persistence-contracts` pull request:

- PostgreSQL-ready SQLAlchemy schema + Alembic forward/rollback migration, local SQLite DB for deterministic tests.
- Configurable OIDC RS256 bearer JWT validation, scopes and fail-closed production config, explicit dev-token mode.
- Owner-filtered journey CRUD, persisted consent/history, session/audit/route/recommendation metadata, deletion and retention function.
- Typed navigation boundaries (simulation, HERE-unavailable, external Maps handoff), typed speech/translation boundary with microphone/consent and request budget checks.
- Flutter typed journey DTOs, token-aware HTTP API, debug-only sign-in, persisted history and resume. No live device access.
- GitHub Actions backend test workflow and Flutter analysis/test workflow.

Verification:

- Backend pytest suite: run `cd services/journey-api && python -m pytest`.
- Flutter SDK absent in authoring container; CI runs bootstrap, `flutter analyze`, `flutter test`. CI results must be checked before claiming mobile tests pass.
- PostgreSQL, real OIDC JWKS endpoint, physical iOS/Android compilation, HERE, Meta and Vantrue hardware are not verified.

See `docs/AUTH_AND_MIGRATIONS.md`, `docs/IMPLEMENTATION_MATRIX.md`, `codex/SPRINT_02.md`.
