#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [[ ! -f "$ROOT/.env.local" ]]; then
  echo "Run python3 scripts/create_dev_config.py once first" >&2
  exit 1
fi
set -a
# shellcheck source=/dev/null
source "$ROOT/.env.local"
set +a
cd "$ROOT/services/journey-api"
alembic -c alembic.ini upgrade head
# Development only: do not bind 0.0.0.0 or expose to public ingress.
uvicorn optilexis_api.main:app --host 127.0.0.1 --port 8000 --reload
