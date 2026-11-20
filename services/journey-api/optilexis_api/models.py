"""Shared request/response contracts for a controlled development prototype."""
from datetime import datetime, timezone
from enum import Enum
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class MobilityMode(str, Enum):
    WALK = "walk"
    DRIVE = "drive"


class NavigationMode(str, Enum):
    OWN_ROUTE = "own_route"
    MAPS_HANDOFF = "maps_handoff"


class JourneyStage(str, Enum):
    STARTED = "started"
    AIRPORT = "airport_approach"
    STATION = "station_approach"
    HOTEL = "hotel_approach"
    PARKING = "parking_approach"
    OFF_ROUTE = "off_route"
    COMPLETE = "completed"


class Consent(BaseModel):
    # User intent only. No sensors are activated by these fields in the starter.
    location: bool = False
    microphone: bool = False
    camera: bool = False


class StartJourney(BaseModel):
    model_config = ConfigDict(extra="forbid")
    destination: str = Field(min_length=2, max_length=160)
    language: Literal["en", "ja", "fr", "es", "de", "zh", "th"] = "ja"
    mode: MobilityMode = MobilityMode.WALK
    navigation_mode: NavigationMode = NavigationMode.MAPS_HANDOFF
    consent: Consent = Field(default_factory=Consent)


class Journey(BaseModel):
    id: UUID
    destination: str
    language: str
    mode: MobilityMode
    navigation_mode: NavigationMode
    consent: Consent
    stage: JourneyStage = JourneyStage.STARTED
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    closed_at: datetime | None = None


class RouteEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")
    event: JourneyStage
    source: Literal["simulation"] = "simulation"
    # A real navigation SDK event adapter must be explicitly implemented later.
    parked: bool = False


class Suggestion(BaseModel):
    id: str
    title: str
    message: str
    action: str
    priority: Literal["navigation", "context"]
    confidence: float = Field(ge=0, le=1)
    source: Literal["simulation"] = "simulation"
    spoken_output_allowed: bool = False


class EventOutcome(BaseModel):
    journey_id: UUID
    event: JourneyStage
    simulated: bool = True
    suppressed: bool
    reason: str | None
    suggestion: Suggestion | None


class PhraseRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    phrase_key: Literal["hotel_checkin", "station_platform", "airport_terminal", "parking_question"]
    language: Literal["en", "ja", "fr", "es", "de", "zh", "th"]


class PhraseResponse(BaseModel):
    source_text: str
    translated_text: str
    language: str
    engine: Literal["curated_demo_phrasebook"] = "curated_demo_phrasebook"
    # The starter does not provide speech recognition or audio generation.
    audio_available: bool = False
