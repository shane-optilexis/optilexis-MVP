# Sprint 02 — identity, migrations, data isolation and retention

## Security architecture

- All journey endpoints enforce `Authorization: Bearer <access_token>` with `journeys:read` or `journeys:write` scopes. A missing/invalid token returns 401; insufficient scope 403.
- `ENV=production` is the **default**. Startup fails without PostgreSQL, OIDC issuer, API audience and HTTPS JWKS endpoint; no anonymous fallback.
- Production JWT validation uses OIDC RS256 signature via cached JWKS, strict issuer, intended API audience, issued-at, expiry and subject checks. Register an **API audience** and send access tokens, not identity tokens. Do not embed OIDC secrets in mobile builds.
- Developer test tokens are supported **only** with `ENV=development` and `ALLOW_DEV_AUTH=true`; values are generated locally, not checked into Git. Never expose debug backend on public IP.
- Every query for journey details, event submission, consent update, close or deletion filters on server-resolved authenticated `user_id`. Foreign and unknown IDs produce identical 404 responses.
- Schema stores identity issuer/sub, journey destination, consent booleans, lifecycle timestamps, simulation decision metadata, and audit action codes. No raw location history, video, microphone data, raw speech text or translation content is persisted.
- For pilot authorization purposes scopes are `journeys:read`, `journeys:write`, `translation:demo`.

## Local developer workflow

```bash
python3 scripts/create_dev_config.py  # first run, outputs local token; .env.local is ignored
python3 -m pip install -r services/journey-api/requirements-dev.txt
./scripts/run_api.sh                 # runs Alembic migration and localhost API
```

In a separate Flutter-enabled terminal:

```bash
./scripts/bootstrap_flutter.sh
cd apps/mobile
flutter run --dart-define=OPTILEXIS_API_URL=http://10.0.2.2:8000
```

Android emulator uses 10.0.2.2; iOS simulator uses 127.0.0.1. **Paste the generated token in the debug app sign-in screen.** Don't put secrets in Dart source or `--dart-define`. The app holds debug token only in memory. Production native OIDC Authorization Code + PKCE and refresh-token handling are a separate deliverable; no fake release login is offered.

## Production readiness steps (not yet cleared)

1. Provision PostgreSQL, perform backup, run `alembic -c alembic.ini upgrade head` with `DATABASE_URL` set.
2. Configure approved OIDC issuer, API audience and JWKS URL; integrate mobile PKCE and secure token storage.
3. Put the service behind TLS ingress with rate limits, security headers and monitoring. Add short-lived JWT acceptance and revocation procedures appropriate to the selected identity provider.
4. Implement a recurring operator-invoked retention job and document data exports/erasure/legal requests. The code offers `purge_closed_journeys` and owned delete endpoints; it does not schedule a background job.
5. Run PostgreSQL integration, iOS/Android build/permission and privacy reviews before pilot deployment.

## Migrations

The initial revision `0001_multiuser_foundation` creates all new tables. No earlier persistent DB exists, so this is a fresh schema; in-memory Sprint 01 journeys cannot be migrated because they were not durable.

```bash
cd services/journey-api
# DATABASE_URL set to the right target.
alembic -c alembic.ini upgrade head
alembic -c alembic.ini current
```

**Rollback:** Back up the database, and only in an isolated disposable environment run `alembic downgrade base` (this drops the entire Sprint 02 schema and **deletes all records**). In environments containing user journeys, use a forward repair migration or restore from a verified backup, not destructive downgrade.

## Privacy and retention

- `DELETE /v1/journeys/{id}` deletes an owned journey and its child route, session, consent and recommendation records.
- `DELETE /v1/me/data` removes all journeys, audit metadata and the current user's database row; subsequent authentication can create a new empty row.
- Audit events contain action codes and resource IDs only. No message payloads, tokens or raw media are logged by app code.
- `purge_closed_journeys(db, retention_days)` deletes closed journeys older than an operator-supplied threshold. It does not run automatically; configure and audit an approved scheduler before production.
- User-initiated consent changes persist but do not itself grant OS-level permissions. No phone location/mic/video is activated in Sprint 02.
