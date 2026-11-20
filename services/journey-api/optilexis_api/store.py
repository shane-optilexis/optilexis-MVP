"""Ephemeral, single-process development store. NOT production persistence."""
from datetime import datetime, timezone
from uuid import UUID, uuid4
from threading import Lock
from .models import Journey, StartJourney, JourneyStage


class JourneyStore:
    def __init__(self) -> None:
        self._rows: dict[UUID, Journey] = {}
        self._lock = Lock()

    def start(self, request: StartJourney) -> Journey:
        with self._lock:
            journey = Journey(id=uuid4(), **request.model_dump())
            self._rows[journey.id] = journey
            return journey.model_copy(deep=True)

    def get(self, journey_id: UUID) -> Journey | None:
        with self._lock:
            j = self._rows.get(journey_id)
            return j.model_copy(deep=True) if j else None

    def list(self) -> list[Journey]:
        with self._lock:
            return [j.model_copy(deep=True) for j in self._rows.values()]

    def update_stage(self, journey_id: UUID, stage: JourneyStage) -> Journey | None:
        with self._lock:
            current = self._rows.get(journey_id)
            if current is None:
                return None
            updated = current.model_copy(update={"stage": stage})
            self._rows[journey_id] = updated
            return updated.model_copy(deep=True)

    def close(self, journey_id: UUID) -> Journey | None:
        with self._lock:
            current = self._rows.get(journey_id)
            if current is None:
                return None
            updated = current.model_copy(update={
                "stage": JourneyStage.COMPLETE,
                "closed_at": datetime.now(timezone.utc),
            })
            self._rows[journey_id] = updated
            return updated.model_copy(deep=True)
