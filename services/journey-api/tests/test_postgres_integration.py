"""Run with TEST_POSTGRES_URL in GitHub Actions' isolated Postgres service.

Skips locally when no PostgreSQL service is configured.
"""
import json
import os
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from alembic.config import Config
from alembic import command
from sqlalchemy import text

from optilexis_api.db import make_engine
from optilexis_api.main import create_app
from optilexis_api.settings import Settings
from .conftest import TOKENS, headers


def test_real_postgresql_migrations_and_owner_isolation(monkeypatch):
    url = os.getenv('TEST_POSTGRES_URL')
    if not url:
        pytest.skip('Dedicated PostgreSQL integration service not available')
    monkeypatch.setenv('DATABASE_URL', url)
    root = Path(__file__).resolve().parents[1]
    cfg = Config(str(root / 'alembic.ini'))
    cfg.set_main_option('script_location', str(root / 'migrations'))
    command.upgrade(cfg, 'head')
    settings = Settings(env='development', database_url=url, allow_dev_auth=True,
                        dev_auth_tokens_json=json.dumps(TOKENS))
    with TestClient(create_app(settings)) as client:
        alice = client.post('/v1/journeys', headers=headers('alice'), json={
            'destination': 'Shinjuku Station, Tokyo', 'language': 'ja'}).json()
        assert alice['id']
        assert client.get(f"/v1/journeys/{alice['id']}", headers=headers('bob')).status_code == 404
        assert client.get(f"/v1/journeys/{alice['id']}", headers=headers('alice')).status_code == 200
    with TestClient(create_app(settings)) as client:
        assert client.get(f"/v1/journeys/{alice['id']}", headers=headers('alice')).status_code == 200
        assert client.post(f"/v1/journeys/{alice['id']}/close", headers=headers('alice')).status_code == 200
        assert client.delete(f"/v1/journeys/{alice['id']}", headers=headers('alice')).status_code == 204
    engine = make_engine(url)
    with engine.connect() as conn:
        assert conn.execute(text('SELECT count(*) FROM journeys')).scalar_one() == 0
    engine.dispose()
