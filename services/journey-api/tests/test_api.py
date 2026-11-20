import pytest
from fastapi.testclient import TestClient
from optilexis_api.main import app


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def create(client, **overrides):
    payload = {
        "destination": "Shinjuku Station, Tokyo",
        "language": "ja",
        "mode": "walk",
        "navigation_mode": "maps_handoff",
        "consent": {"location": False, "microphone": False, "camera": False},
    }
    payload.update(overrides)
    response = client.post("/v1/journeys", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def test_health_and_capability_disclosures(client):
    assert client.get("/health").json() == {"status": "ok", "environment": "development_simulation"}
    caps = client.get("/v1/capabilities").json()
    assert caps["vantrue_live_video"] == "unverified_no_integration"
    assert caps["speech_translation"] == "not_integrated"


def test_create_and_retrieve_a_journey(client):
    j = create(client)
    assert j["stage"] == "started"
    assert client.get(f"/v1/journeys/{j['id']}").json()["destination"] == "Shinjuku Station, Tokyo"
    assert any(item["id"] == j["id"] for item in client.get("/v1/journeys").json())


def test_walking_event_produces_simulated_recommendation(client):
    j = create(client)
    resp = client.post(f"/v1/journeys/{j['id']}/events", json={"event": "station_approach", "source": "simulation"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["simulated"] and not data["suppressed"]
    assert data["suggestion"]["title"] == "Railway station"
    assert data["suggestion"]["spoken_output_allowed"] is False


def test_driving_suppresses_nonessential_prompt_until_parked(client):
    j = create(client, mode="drive")
    url = f"/v1/journeys/{j['id']}/events"
    moving = client.post(url, json={"event": "hotel_approach", "parked": False}).json()
    assert moving["suppressed"] is True
    assert moving["suggestion"] is None
    parked = client.post(url, json={"event": "hotel_approach", "parked": True}).json()
    assert parked["suppressed"] is False
    assert parked["suggestion"]["priority"] == "context"


def test_off_route_suggestion_does_not_fabricate_turn(client):
    j = create(client, mode="drive")
    data = client.post(f"/v1/journeys/{j['id']}/events", json={"event": "off_route"}).json()
    assert data["suggestion"]["priority"] == "navigation"
    assert "Recalculate" in data["suggestion"]["message"]


def test_end_trip_prevents_more_events(client):
    j = create(client)
    end = client.post(f"/v1/journeys/{j['id']}/close")
    assert end.status_code == 200
    assert end.json()["closed_at"] is not None
    assert client.post(f"/v1/journeys/{j['id']}/events", json={"event": "hotel_approach"}).status_code == 409


def test_demo_phrasebook_translates_only_curated_phrases(client):
    resp = client.post("/v1/translation/demo-phrase", json={"phrase_key": "hotel_checkin", "language": "fr"})
    assert resp.status_code == 200
    assert "réservation" in resp.json()["translated_text"]
    assert resp.json()["engine"] == "curated_demo_phrasebook"
    assert not resp.json()["audio_available"]


def test_no_fake_live_translation(client):
    assert client.post("/v1/translation/freeform").status_code == 501


def test_validations_and_closed_cannot_be_reopened(client):
    assert client.post("/v1/journeys", json={"destination": "x"}).status_code == 422
    assert client.post("/v1/journeys", json={"destination": "Tokyo", "unexpected": True}).status_code == 422
    assert client.post("/v1/journeys", json={"destination": "Tokyo", "language": "xx"}).status_code == 422
    j = create(client)
    assert client.post(f"/v1/journeys/{j['id']}/events", json={"event": "hotel_approach", "source": "scraped_google_maps"}).status_code == 422
