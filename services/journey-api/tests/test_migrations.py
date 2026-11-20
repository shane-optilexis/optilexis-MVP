from pathlib import Path
from alembic import command
from alembic.config import Config
from sqlalchemy import inspect
from optilexis_api.db import make_engine
from .conftest import migrated_db


def test_alembic_upgrade_and_destructive_downgrade_on_empty_temp_db(tmp_path, monkeypatch):
    url = migrated_db(monkeypatch, tmp_path / 'migration.sqlite')
    root = Path(__file__).resolve().parents[1]
    cfg = Config(str(root / 'alembic.ini'))
    cfg.set_main_option('script_location', str(root / 'migrations'))
    engine = make_engine(url)
    assert {'users', 'journeys', 'journey_sessions', 'consents', 'routes',
            'recommendation_events', 'audit_events'} <= set(inspect(engine).get_table_names())
    engine.dispose()
    command.downgrade(cfg, 'base')
    engine = make_engine(url)
    assert 'journeys' not in inspect(engine).get_table_names()
    engine.dispose()
