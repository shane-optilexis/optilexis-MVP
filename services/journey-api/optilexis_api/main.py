"""Optilexis journey API — development-only backend.

SECURITY: no authentication or durable persistence yet. Keep bound to loopback;
do not place on a publicly reachable server.
"""
from contextlib import asynccontextmanager
from uuid import UUID
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from .models import (Journey, StartJourney, RouteEvent, EventOutcome,
                     PhraseRequest, PhraseResponse, JourneyStage)
from .store import JourneyStore
from .predictor import assess_event
from .phrases import phrase_for


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.store = JourneyStore()
    yield


app = FastAPI(
    title="Optilexis Journey API", version="0.1.0", lifespan=lifespan,
    description="Development simulator; not a connected navigation or translation service.",
)


class ServiceStatus(BaseModel):
    status: str
    environment: str


@app.get("/health", response_model=ServiceStatus)
def health() -> ServiceStatus:
    return ServiceStatus(status="ok", environment="development_simulation")


@app.get("/v1/capabilities")
def capabilities() -> dict:
    return {
        "journeys": "development_simulator",
        "navigation": "maps_handoff_only; own_route_sdk_not_integrated",
        "speech_translation": "not_integrated",
        "phrasebook": "curated_demo",
        "meta_wearables": "not_integrated",
        "vantrue_live_video": "unverified_no_integration",
        "carplay_android_auto": "not_integrated",
    }


@app.post("/v1/journeys", response_model=Journey, status_code=status.HTTP_201_CREATED)
def start_journey(request: StartJourney) -> Journey:
    return app.state.store.start(request)


@app.get("/v1/journeys", response_model=list[Journey])
def list_journeys() -> list[Journey]:
    # Only suitable for loopback testing: no multiuser access control.
    return app.state.store.list()


@app.get("/v1/journeys/{journey_id}", response_model=Journey)
def get_journey(journey_id: UUID) -> Journey:
    journey = app.state.store.get(journey_id)
    if journey is None:
        raise HTTPException(status_code=404, detail="Journey not found")
    return journey


@app.post("/v1/journeys/{journey_id}/events", response_model=EventOutcome)
def submit_simulated_event(journey_id: UUID, event: RouteEvent) -> EventOutcome:
    journey = get_journey(journey_id)
    if journey.closed_at is not None:
        raise HTTPException(status_code=409, detail="Journey already closed")
    outcome = assess_event(journey, event)
    app.state.store.update_stage(journey_id, event.event)
    if event.event == JourneyStage.COMPLETE:
        app.state.store.close(journey_id)
    return outcome


@app.post("/v1/journeys/{journey_id}/close", response_model=Journey)
def close_journey(journey_id: UUID) -> Journey:
    existing = get_journey(journey_id)
    if existing.closed_at is not None:
        raise HTTPException(status_code=409, detail="Journey already closed")
    result = app.state.store.close(journey_id)
    assert result is not None
    return result


@app.post("/v1/translation/demo-phrase", response_model=PhraseResponse)
def demo_phrase(request: PhraseRequest) -> PhraseResponse:
    return phrase_for(request)


@app.post("/v1/translation/freeform", status_code=status.HTTP_501_NOT_IMPLEMENTED)
def unconfigured_translation() -> dict:
    raise HTTPException(status_code=501, detail="Speech and freeform translation providers are not configured")
