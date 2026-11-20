"""Optilexis Sprint 02 authenticated, durable journey API.

No GPS, OIDC client registration, live translation or hardware data are faked.
Migrate the configured database before running. Never expose development token
mode outside a controlled loopback/emulator environment.
"""
from contextlib import asynccontextmanager
from typing import Annotated
from uuid import UUID

from fastapi import Depends, FastAPI, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .auth import Principal, require_scope
from .db import make_engine, session_factory
from .models import (Journey, StartJourney, RouteEvent, EventOutcome,
                     PhraseRequest, PhraseResponse, JourneyStage, ConsentPatch)
from .repository import JourneyRepository
from .predictor import assess_event
from .translation import CuratedPhraseProvider
from .live_text import LiveTextRequest, LiveTextResponse, AzureTextTranslator, LiveTextUnavailable
from .settings import Settings


def get_db(request: Request):
    with request.app.state.db_session_factory() as db:
        yield db


def owner_repo(db: Session, principal: Principal) -> JourneyRepository:
    return JourneyRepository(db, principal)


class ServiceStatus(BaseModel):
    status: str
    environment: str


def create_app(settings_override: Settings | None = None,
               text_translator_override: AzureTextTranslator | None = None) -> FastAPI:
    @asynccontextmanager
    async def lifespan(application: FastAPI):
        settings = settings_override or Settings.from_env()
        settings.validate()
        engine = make_engine(settings.database_url)
        application.state.settings = settings
        application.state.engine = engine
        application.state.db_session_factory = session_factory(engine)
        # Deliberately no Base.metadata.create_all: Alembic migrations are mandatory.
        try:
            yield
        finally:
            engine.dispose()

    api = FastAPI(title="Optilexis Journey API", version="0.2.0", lifespan=lifespan,
                  description="Authenticated pilot foundation. Provider events still simulated.")

    @api.get("/health", response_model=ServiceStatus)
    def health(request: Request) -> ServiceStatus:
        return ServiceStatus(status="ok", environment=request.app.state.settings.env)

    @api.get("/v1/capabilities")
    def capabilities(request: Request) -> dict:
        return {
            "journeys": "authenticated_persistent",
            "navigation": "maps_handoff_only; here_sdk_not_integrated",
            "simulation": "development_only" if request.app.state.settings.env == "development" else "disabled",
            "speech_translation": "not_integrated",
            "text_translation": ("azure_configured_unverified" if request.app.state.settings.text_translator == "azure" else "disabled"),
            "phrasebook": "curated_demo",
            "meta_wearables": "not_integrated",
            "vantrue_live_video": "unverified_no_integration",
            "carplay_android_auto": "not_integrated",
        }

    @api.post("/v1/journeys", response_model=Journey, status_code=status.HTTP_201_CREATED)
    def start_journey(payload: StartJourney, principal: Principal = Depends(require_scope("journeys:write")),
                      db: Session = Depends(get_db)) -> Journey:
        return owner_repo(db, principal).start(payload)

    @api.get("/v1/journeys", response_model=list[Journey])
    def list_journeys(principal: Principal = Depends(require_scope("journeys:read")),
                      db: Session = Depends(get_db)) -> list[Journey]:
        return owner_repo(db, principal).list()

    def owned(repo: JourneyRepository, journey_id: UUID) -> Journey:
        journey = repo.get(journey_id)
        if journey is None:
            raise HTTPException(status_code=404, detail="Journey not found")
        return journey

    @api.get("/v1/journeys/{journey_id}", response_model=Journey)
    def get_journey(journey_id: UUID, principal: Principal = Depends(require_scope("journeys:read")),
                    db: Session = Depends(get_db)) -> Journey:
        return owned(owner_repo(db, principal), journey_id)

    @api.post("/v1/journeys/{journey_id}/events", response_model=EventOutcome)
    def simulated_event(journey_id: UUID, event: RouteEvent, request: Request,
                        principal: Principal = Depends(require_scope("journeys:write")),
                        db: Session = Depends(get_db)) -> EventOutcome:
        if request.app.state.settings.env != "development":
            raise HTTPException(status_code=404, detail="Not found")
        repo = owner_repo(db, principal)
        journey = owned(repo, journey_id)
        if journey.closed_at is not None:
            raise HTTPException(status_code=409, detail="Journey already closed")
        outcome = assess_event(journey, event)
        repo.record_event(journey_id, outcome)
        return outcome

    @api.post("/v1/journeys/{journey_id}/close", response_model=Journey)
    def close_journey(journey_id: UUID, principal: Principal = Depends(require_scope("journeys:write")),
                      db: Session = Depends(get_db)) -> Journey:
        repo = owner_repo(db, principal)
        current = owned(repo, journey_id)
        if current.closed_at is not None:
            raise HTTPException(status_code=409, detail="Journey already closed")
        result = repo.close(journey_id)
        assert result is not None
        return result

    @api.patch("/v1/journeys/{journey_id}/consent", response_model=Journey)
    def update_consent(journey_id: UUID, new_consent: ConsentPatch,
                       principal: Principal = Depends(require_scope("journeys:write")),
                       db: Session = Depends(get_db)) -> Journey:
        repo = owner_repo(db, principal)
        current = owned(repo, journey_id)
        if current.closed_at is not None:
            raise HTTPException(status_code=409, detail="Journey already closed")
        result = repo.consent(journey_id, new_consent)
        assert result is not None
        return result

    @api.delete("/v1/journeys/{journey_id}", status_code=status.HTTP_204_NO_CONTENT)
    def delete_journey(journey_id: UUID, principal: Principal = Depends(require_scope("journeys:write")),
                       db: Session = Depends(get_db)) -> None:
        if not owner_repo(db, principal).delete(journey_id):
            raise HTTPException(status_code=404, detail="Journey not found")

    @api.delete("/v1/me/data", status_code=status.HTTP_204_NO_CONTENT)
    def delete_my_data(principal: Principal = Depends(require_scope("journeys:write")),
                       db: Session = Depends(get_db)) -> None:
        owner_repo(db, principal).delete_my_data()

    @api.post("/v1/translation/demo-phrase", response_model=PhraseResponse)
    def demo_phrase(payload: PhraseRequest,
                    principal: Principal = Depends(require_scope("translation:demo"))) -> PhraseResponse:
        return CuratedPhraseProvider().lookup(payload)

    @api.post("/v1/translation/text", response_model=LiveTextResponse)
    async def translate_text(payload: LiveTextRequest, request: Request,
                             principal: Principal = Depends(require_scope("translation:live")),
                             db: Session = Depends(get_db)) -> LiveTextResponse:
        if not payload.user_activated:
            raise HTTPException(status_code=403, detail="Explicit user action is required")
        journey = owner_repo(db, principal).get(payload.journey_id)
        if journey is None:
            raise HTTPException(status_code=404, detail="Journey not found")
        if journey.closed_at is not None:
            raise HTTPException(status_code=409, detail="Journey already closed")
        if journey.mode.value == "drive":
            raise HTTPException(status_code=409, detail="Typing while driving is disabled")
        if len(payload.text.encode("utf-8")) > 1000:
            raise HTTPException(status_code=413, detail="Input too long")
        settings = request.app.state.settings
        if settings.text_translator != "azure":
            raise HTTPException(status_code=503, detail="Text translation is not configured")
        provider = text_translator_override or AzureTextTranslator(
            endpoint=settings.azure_translator_endpoint,
            key=settings.azure_translator_key,
            region=settings.azure_translator_region,
        )
        try:
            result = await provider.translate(payload.text, payload.source_language, payload.target_language)
        except LiveTextUnavailable:
            raise HTTPException(status_code=503, detail="Translation temporarily unavailable") from None
        return LiveTextResponse(translated_text=result,
                                source_language=payload.source_language,
                                target_language=payload.target_language)

    @api.post("/v1/translation/freeform", status_code=501)
    def unconfigured_translation(principal: Principal = Depends(require_scope("translation:demo"))) -> dict:
        raise HTTPException(status_code=501, detail="ASR, translation and speech providers are not configured")

    return api


app = create_app()
