import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from alembic import command
from alembic.config import Config

from optilexis_api.main import create_app
from optilexis_api.settings import Settings

TOKENS = {
    "local-test-alice-access-token-00000001": {"sub": "alice", "scope": "journeys:read journeys:write translation:demo"},
    "local-test-bob-access-token-0000000002": {"sub": "bob", "scope": "journeys:read journeys:write translation:demo"},
    "local-test-readonly-access-token-0003": {"sub": "readonly", "scope": "journeys:read"},
}


def headers(user="alice"):
    names = {"alice": "local-test-alice-access-token-00000001",
             "bob": "local-test-bob-access-token-0000000002",
             "readonly": "local-test-readonly-access-token-0003"}
    return {"Authorization": f"Bearer {names[user]}"}


def migrated_db(monkeypatch, path: Path) -> str:
    url = f"sqlite+pysqlite:///{path}"
    monkeypatch.setenv("DATABASE_URL", url)
    alembic_dir = Path(__file__).resolve().parents[1]
    cfg = Config(str(alembic_dir / "alembic.ini"))
    cfg.set_main_option("script_location", str(alembic_dir / "migrations"))
    command.upgrade(cfg, "head")
    return url


@pytest.fixture
def settings(tmp_path, monkeypatch):
    url = migrated_db(monkeypatch, tmp_path / "optilexis.sqlite")
    return Settings(env="development", database_url=url, allow_dev_auth=True,
                    dev_auth_tokens_json=json.dumps(TOKENS))


@pytest.fixture
def client(settings):
    with TestClient(create_app(settings)) as c:
        yield c
