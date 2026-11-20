#!/usr/bin/env python3
"""Generate a LOCAL-only dev token and database config; no committed defaults."""
import json
import secrets
import shlex
from pathlib import Path

root = Path(__file__).resolve().parents[1]
output = root / '.env.local'
if output.exists():
    raise SystemExit(f'{output} already exists; refusing to overwrite credentials')
folder = root / 'services' / 'journey-api' / 'var'
folder.mkdir(parents=True, exist_ok=True)
token = secrets.token_urlsafe(32)
identity = {token: {'sub': 'local-pilot-user', 'scope': 'journeys:read journeys:write translation:demo translation:live'}}
values = {
    'ENV': 'development',
    'DATABASE_URL': f'sqlite+pysqlite:///{folder / "optilexis.sqlite"}',
    'ALLOW_DEV_AUTH': 'true',
    'DEV_AUTH_TOKENS_JSON': json.dumps(identity, separators=(',', ':')),
}
output.write_text('\n'.join(f'{key}={shlex.quote(value)}' for key, value in values.items()) + '\n')
output.chmod(0o600)
print(f'Created {output} (permissions 0600).')
print('Paste this token into the DEBUG app sign-in screen; do not commit, share, or use on public servers:')
print(token)
