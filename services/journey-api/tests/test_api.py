from fastapi.testclient import TestClient
from optilexis_api.main import create_app
from .conftest import headers


def create(client, user="alice", **overrides):
    payload = {
        "destination": "Shinjuku Station, Tokyo", "language": "ja", "mode": "walk",
        "navigation_mode": "maps_handoff",
        "consent": {"location": False, "microphone": False, "camera": False},
    }
    payload.update(overrides)
    response = client.post("/v1/journeys", json=payload, headers=headers(user))
    assert response.status_code == 201, response.text
    return response.json()


def test_health_and_truthful_capabilities(client):
    assert client.get("/health").json() == {"status": "ok", "environment": "development"}
    caps = client.get("/v1/capabilities").json()
    assert caps["journeys"] == "authenticated_persistent"
    assert caps["vantrue_live_video"] == "unverified_no_integration"
    assert caps["speech_translation"] == "not_integrated"


def test_missing_invalid_and_insufficient_tokens(client):
    assert client.get("/v1/journeys").status_code == 401
    assert client.get("/v1/journeys", headers={"Authorization": "Bearer wrong-token"}).status_code == 401
    assert client.post("/v1/journeys", json={"destination": "Tokyo"}, headers=headers("readonly")).status_code == 403
    assert client.get("/v1/journeys", headers=headers("readonly")).status_code == 200


def test_create_retrieve_list_user_owned(client):
    j = create(client)
    assert j["stage"] == "started"
    assert client.get(f"/v1/journeys/{j['id']}", headers=headers()).json()["destination"] == "Shinjuku Station, Tokyo"
    assert [item["id"] for item in client.get("/v1/journeys", headers=headers()).json()] == [j["id"]]


def test_tenant_isolation_works_on_all_journey_endpoints(client):
    alice = create(client)
    bob = create(client, user="bob", destination="Paris Hotel")
    assert [x["id"] for x in client.get("/v1/journeys", headers=headers("bob")).json()] == [bob["id"]]
    for path in [f"/v1/journeys/{alice['id']}"]:
        assert client.get(path, headers=headers("bob")).status_code == 404
    assert client.post(f"/v1/journeys/{alice['id']}/close", headers=headers("bob")).status_code == 404
    assert client.post(f"/v1/journeys/{alice['id']}/events", headers=headers("bob"),
                       json={"event": "station_approach", "source": "simulation"}).status_code == 404
    assert client.patch(f"/v1/journeys/{alice['id']}/consent", headers=headers("bob"),
                        json={"microphone": True}).status_code == 404
    assert client.delete(f"/v1/journeys/{alice['id']}", headers=headers("bob")).status_code == 404
    assert client.get(f"/v1/journeys/{alice['id']}", headers=headers()).status_code == 200


def test_persistence_across_app_restart(settings):
    with TestClient(create_app(settings)) as c:
        j = create(c)
    with TestClient(create_app(settings)) as c2:
        assert c2.get(f"/v1/journeys/{j['id']}", headers=headers()).json()["destination"] == j["destination"]
        assert c2.post(f"/v1/journeys/{j['id']}/close", headers=headers()).status_code == 200
    with TestClient(create_app(settings)) as c3:
        assert c3.get(f"/v1/journeys/{j['id']}", headers=headers()).json()["closed_at"] is not None


def test_walking_event_is_explicitly_simulated(client):
    j = create(client)
    resp = client.post(f"/v1/journeys/{j['id']}/events", headers=headers(),
                       json={"event": "station_approach", "source": "simulation"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["simulated"] and not data["suppressed"]
    assert data["suggestion"]["title"] == "Railway station"
    assert data["suggestion"]["spoken_output_allowed"] is False
    assert client.post(f"/v1/journeys/{j['id']}/events", headers=headers(),
                       json={"event": "hotel_approach", "source": "real_here"}).status_code == 422


def test_driving_suppresses_nonessential_prompt_until_parked(client):
    j = create(client, mode="drive")
    url = f"/v1/journeys/{j['id']}/events"
    moving = client.post(url, headers=headers(), json={"event": "hotel_approach", "parked": False}).json()
    assert moving["suppressed"] is True and moving["suggestion"] is None
    parked = client.post(url, headers=headers(), json={"event": "hotel_approach", "parked": True}).json()
    assert parked["suppressed"] is False and parked["suggestion"]["priority"] == "context"


def test_off_route_does_not_fabricate_turn(client):
    j = create(client, mode="drive")
    data = client.post(f"/v1/journeys/{j['id']}/events", headers=headers(),
                       json={"event": "off_route"}).json()
    assert data["suggestion"]["priority"] == "navigation"
    assert "Recalculate" in data["suggestion"]["message"]


def test_close_prevents_more_events_and_consent_updates(client):
    j = create(client)
    end = client.post(f"/v1/journeys/{j['id']}/close", headers=headers())
    assert end.status_code == 200 and end.json()["closed_at"] is not None
    assert client.post(f"/v1/journeys/{j['id']}/events", headers=headers(),
                       json={"event": "hotel_approach"}).status_code == 409
    assert client.patch(f"/v1/journeys/{j['id']}/consent", headers=headers(),
                        json={"camera": True}).status_code == 409


def test_explicit_consent_update_and_deletion(client):
    j = create(client)
    changed = client.patch(f"/v1/journeys/{j['id']}/consent", headers=headers(),
                           json={"location": True, "microphone": True, "camera": False})
    assert changed.status_code == 200 and changed.json()["consent"]["microphone"] is True
    later = client.patch(f"/v1/journeys/{j['id']}/consent", headers=headers(), json={"camera": True})
    assert later.status_code == 200 and later.json()["consent"]["microphone"] is True
    assert later.json()["consent"]["camera"] is True
    assert client.delete(f"/v1/journeys/{j['id']}", headers=headers()).status_code == 204
    assert client.get(f"/v1/journeys/{j['id']}", headers=headers()).status_code == 404


def test_deleting_my_data_does_not_delete_other_users(client):
    alice = create(client)
    bob = create(client, user="bob")
    assert client.delete("/v1/me/data", headers=headers()).status_code == 204
    assert client.get(f"/v1/journeys/{alice['id']}", headers=headers()).status_code == 404
    assert client.get(f"/v1/journeys/{bob['id']}", headers=headers("bob")).status_code == 200


def test_phrasebook_uses_scope_and_unconfigured_speech_is_501(client):
    payload = {"phrase_key": "hotel_checkin", "language": "fr"}
    assert client.post("/v1/translation/demo-phrase", json=payload).status_code == 401
    assert client.post("/v1/translation/demo-phrase", json=payload, headers=headers("readonly")).status_code == 403
    resp = client.post("/v1/translation/demo-phrase", json=payload, headers=headers())
    assert resp.status_code == 200 and "réservation" in resp.json()["translated_text"]
    assert resp.json()["engine"] == "curated_demo_phrasebook" and not resp.json()["audio_available"]
    assert client.post("/v1/translation/freeform", headers=headers()).status_code == 501


def test_validation_and_no_automatic_ownership_override(client):
    assert client.post("/v1/journeys", json={"destination": "x"}, headers=headers()).status_code == 422
    assert client.post("/v1/journeys", json={"destination": "Tokyo", "unexpected": True}, headers=headers()).status_code == 422
    assert client.post("/v1/journeys", json={"destination": "Tokyo", "language": "xx"}, headers=headers()).status_code == 422
    assert client.post("/v1/journeys", json={"destination": "Tokyo", "user_id": "bob"}, headers=headers()).status_code == 422
