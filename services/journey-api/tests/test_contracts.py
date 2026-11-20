import asyncio
from datetime import datetime, timedelta, timezone
from uuid import uuid4
import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session
from optilexis_api.settings import Settings
from optilexis_api.auth import verify_bearer
from optilexis_api.navigation import (SimulatedNavigationProvider, HereNavigateBoundary,
    MapsHandoffBoundary, LocationPermissionDenied, NavigationUnavailable, NavigationSource)
from optilexis_api.translation import (TranslationPolicy, ConsentRequired,
    TranslationUnavailable, transcribe_with_policy)
from optilexis_api.repository import purge_closed_journeys
from optilexis_api.db import JourneyRecord, RecommendationRecord, AuditRecord
from .conftest import headers
from .test_api import create


def test_fail_closed_production_configuration():
    with pytest.raises(ValueError):
        Settings(env="production", database_url="sqlite:///tmp.db", allow_dev_auth=True,
                 dev_auth_tokens_json='{"abcdabcdabcdabcdabcdabcd":{"sub":"user"}}').validate()
    with pytest.raises(ValueError):
        Settings(env="production", database_url="sqlite:///tmp.db").validate()
    with pytest.raises(ValueError):
        Settings(env="development", database_url="sqlite:///tmp.db", allow_dev_auth=False).validate()


def test_only_configured_dev_token_is_accepted(settings):
    with pytest.raises(HTTPException) as ex:
        verify_bearer("not-a-token", settings)
    assert ex.value.status_code == 401
    assert verify_bearer("local-test-alice-access-token-00000001", settings).subject == "alice"


def test_simulation_provider_cannot_masquerade_as_here():
    async def check():
        jid = uuid4()
        mock = SimulatedNavigationProvider(["hotel_approach", "off_route"])
        await mock.start_route(jid, location_permission_granted=False)
        events = [x async for x in mock.subscribe(jid)]
        assert all(x.simulated and x.source is NavigationSource.SIMULATION for x in events)
        await mock.stop_route(jid)
        with pytest.raises(LocationPermissionDenied):
            await HereNavigateBoundary().start_route(jid, location_permission_granted=False)
        with pytest.raises(NavigationUnavailable):
            await HereNavigateBoundary().start_route(jid, location_permission_granted=True)
        with pytest.raises(NavigationUnavailable):
            await MapsHandoffBoundary().start_route(jid, location_permission_granted=True)
    asyncio.run(check())


def test_microphone_policy_and_timeout_do_not_log_raw_content():
    class Transcriber:
        async def transcribe(self, audio, language):
            await asyncio.sleep(.02)
            return "not logged"
    async def check():
        recorded = []
        policy = TranslationPolicy(True, False, True)
        with pytest.raises(ConsentRequired):
            await transcribe_with_policy(Transcriber(), b"audio", "en", policy,
                                         lambda status, ms: recorded.append((status, ms)))
        assert not recorded
        short = TranslationPolicy(True, True, True, timeout_seconds=.001)
        with pytest.raises(TranslationUnavailable, match="timed out"):
            await transcribe_with_policy(Transcriber(), b"audio", "en", short,
                                         lambda status, ms: recorded.append((status, ms)))
        assert recorded[0][0] == "timeout" and len(recorded[0]) == 2
    asyncio.run(check())


def test_recommendation_records_and_retention_purge(client):
    j = create(client)
    client.post(f"/v1/journeys/{j['id']}/events", json={"event": "station_approach"}, headers=headers())
    client.post(f"/v1/journeys/{j['id']}/close", headers=headers())
    with client.app.state.db_session_factory() as db:
        assert db.query(RecommendationRecord).count() == 1
        assert db.query(AuditRecord).count() >= 2
        row = db.get(JourneyRecord, j["id"])
        row.closed_at = datetime.now(timezone.utc) - timedelta(days=40)
        db.commit()
        assert purge_closed_journeys(db, retention_days=30) == 1
        assert db.query(RecommendationRecord).count() == 0
