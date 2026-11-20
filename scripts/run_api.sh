#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT/services/journey-api"
exec python -m uvicorn optilexis_api.main:app --host 127.0.0.1 --port 8000 --reload
