"""Owner-scoped durable journey repository.

Every read/mutation is explicitly filtered by the authenticated issuer/subject's
resolved user ID. A missing or foreign journey uniformly returns None (HTTP 404).
"""
from datetime import datetime, timedelta, timezone
from uuid import UUID
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from .auth import Principal
from .db import (UserRecord, JourneyRecord, ConsentRecord, RouteRecord,
                 JourneySessionRecord, RecommendationRecord, AuditRecord, utcnow)
from .models import Journey, StartJourney, JourneyStage, Consent, ConsentPatch, EventOutcome


def as_utc(value: datetime | None) -> datetime | None:
    if value is not None and value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


class JourneyRepository:
    def __init__(self, db: Session, principal: Principal):
        self.db = db
        self.principal = principal
        self.user_id = self._ensure_user()

    def _ensure_user(self) -> str:
        query = select(UserRecord).where(UserRecord.issuer == self.principal.issuer,
                                         UserRecord.subject == self.principal.subject)
        user = self.db.scalar(query)
        if user is None:
            user = UserRecord(issuer=self.principal.issuer, subject=self.principal.subject)
            self.db.add(user)
            try:
                self.db.commit()
            except IntegrityError:
                self.db.rollback()
                user = self.db.scalar(query)
                if user is None:
                    raise
        return user.id

    def _owned(self, journey_id: UUID) -> JourneyRecord | None:
        return self.db.scalar(select(JourneyRecord).options(selectinload(JourneyRecord.consent)).where(
            JourneyRecord.id == str(journey_id), JourneyRecord.user_id == self.user_id))

    @staticmethod
    def _convert(row: JourneyRecord) -> Journey:
        return Journey(
            id=UUID(row.id), destination=row.destination, language=row.language,
            mode=row.mode, navigation_mode=row.navigation_mode,
            consent=Consent(location=row.consent.location, microphone=row.consent.microphone,
                            camera=row.consent.camera), stage=row.stage,
            created_at=as_utc(row.created_at), closed_at=as_utc(row.closed_at),
        )

    def _audit(self, action: str, journey_id: str | None = None):
        self.db.add(AuditRecord(user_id=self.user_id, action=action, resource_id=journey_id))

    def start(self, payload: StartJourney) -> Journey:
        row = JourneyRecord(
            user_id=self.user_id, destination=payload.destination, language=payload.language,
            mode=payload.mode.value, navigation_mode=payload.navigation_mode.value,
            stage=JourneyStage.STARTED.value,
            consent=ConsentRecord(**payload.consent.model_dump()),
            route=RouteRecord(provider="maps_handoff" if payload.navigation_mode.value == "maps_handoff" else "here_sdk_pending"),
            sessions=[JourneySessionRecord()],
        )
        self.db.add(row)
        self.db.flush()
        self._audit("journey_created", row.id)
        self.db.commit()
        self.db.refresh(row)
        return self._convert(row)

    def get(self, journey_id: UUID) -> Journey | None:
        row = self._owned(journey_id)
        return self._convert(row) if row else None

    def list(self) -> list[Journey]:
        rows = self.db.scalars(select(JourneyRecord).options(selectinload(JourneyRecord.consent)).where(
            JourneyRecord.user_id == self.user_id).order_by(JourneyRecord.created_at.desc())).all()
        return [self._convert(row) for row in rows]

    def record_event(self, journey_id: UUID, outcome: EventOutcome) -> Journey | None:
        row = self._owned(journey_id)
        if row is None:
            return None
        row.stage = outcome.event.value
        self.db.add(RecommendationRecord(
            journey_id=row.id, stage=outcome.event.value, source="simulation",
            suppressed=outcome.suppressed,
            reason_code=("safety_suppressed" if outcome.suppressed and outcome.reason and "Driving" in outcome.reason
                         else "not_relevant" if outcome.suppressed else None),
        ))
        if outcome.event == JourneyStage.COMPLETE:
            self._finish(row)
        self._audit("simulated_event", row.id)
        self.db.commit()
        return self._convert(row)

    def _finish(self, row: JourneyRecord) -> None:
        row.stage = JourneyStage.COMPLETE.value
        row.closed_at = utcnow()
        for session in self.db.scalars(select(JourneySessionRecord).where(JourneySessionRecord.journey_id == row.id)):
            session.ended_at = row.closed_at

    def close(self, journey_id: UUID) -> Journey | None:
        row = self._owned(journey_id)
        if row is None:
            return None
        self._finish(row)
        self._audit("journey_closed", row.id)
        self.db.commit()
        return self._convert(row)

    def consent(self, journey_id: UUID, consent: ConsentPatch) -> Journey | None:
        row = self._owned(journey_id)
        if row is None:
            return None
        for key, value in consent.model_dump(exclude_unset=True).items():
            if value is not None:
                setattr(row.consent, key, value)
        row.consent.updated_at = utcnow()
        self._audit("consent_updated", row.id)
        self.db.commit()
        return self._convert(row)

    def delete(self, journey_id: UUID) -> bool:
        row = self._owned(journey_id)
        if row is None:
            return False
        self._audit("journey_deleted", row.id)
        self.db.delete(row)
        self.db.commit()
        return True

    def delete_my_data(self) -> None:
        user = self.db.get(UserRecord, self.user_id)
        if user is not None:
            self.db.delete(user)
            self.db.commit()


def purge_closed_journeys(db: Session, retention_days: int, now: datetime | None = None) -> int:
    """Explicit, operator-invoked retention sweep. Not a background scheduler."""
    cutoff = (now or utcnow()) - timedelta(days=retention_days)
    rows = db.scalars(select(JourneyRecord).where(JourneyRecord.closed_at.is_not(None), JourneyRecord.closed_at < cutoff)).all()
    for row in rows:
        db.delete(row)
    db.commit()
    return len(rows)
