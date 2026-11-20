"""Relational model for authenticated, durable journey sessions.

No audio, raw transcripts, GPS trails, or video are persisted by this schema.
"""
from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy import DateTime, ForeignKey, Index, String, Text, Boolean, Float, Integer, create_engine, event
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker
from sqlalchemy.engine import Engine


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def new_id() -> str:
    return str(uuid4())


class Base(DeclarativeBase):
    pass


class UserRecord(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    issuer: Mapped[str] = mapped_column(String(255), nullable=False)
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    __table_args__ = (Index("ux_users_issuer_subject", "issuer", "subject", unique=True),)
    journeys = relationship("JourneyRecord", cascade="all, delete-orphan", passive_deletes=True)


class JourneyRecord(Base):
    __tablename__ = "journeys"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    destination: Mapped[str] = mapped_column(String(160), nullable=False)
    language: Mapped[str] = mapped_column(String(8), nullable=False)
    mode: Mapped[str] = mapped_column(String(10), nullable=False)
    navigation_mode: Mapped[str] = mapped_column(String(32), nullable=False)
    stage: Mapped[str] = mapped_column(String(40), nullable=False, default="started")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    consent = relationship("ConsentRecord", uselist=False, cascade="all, delete-orphan", passive_deletes=True)
    route = relationship("RouteRecord", uselist=False, cascade="all, delete-orphan", passive_deletes=True)
    sessions = relationship("JourneySessionRecord", cascade="all, delete-orphan", passive_deletes=True)
    recommendation_events = relationship("RecommendationRecord", cascade="all, delete-orphan", passive_deletes=True)


class ConsentRecord(Base):
    __tablename__ = "consents"
    journey_id: Mapped[str] = mapped_column(String(36), ForeignKey("journeys.id", ondelete="CASCADE"), primary_key=True)
    location: Mapped[bool] = mapped_column(Boolean, default=False)
    microphone: Mapped[bool] = mapped_column(Boolean, default=False)
    camera: Mapped[bool] = mapped_column(Boolean, default=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class RouteRecord(Base):
    __tablename__ = "routes"
    journey_id: Mapped[str] = mapped_column(String(36), ForeignKey("journeys.id", ondelete="CASCADE"), primary_key=True)
    provider: Mapped[str] = mapped_column(String(35), nullable=False)
    real_route_started: Mapped[bool] = mapped_column(Boolean, default=False)
    # Do not fabricate SDK steps, route coordinates or ETA.


class JourneySessionRecord(Base):
    __tablename__ = "journey_sessions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    journey_id: Mapped[str] = mapped_column(String(36), ForeignKey("journeys.id", ondelete="CASCADE"), index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class RecommendationRecord(Base):
    __tablename__ = "recommendation_events"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    journey_id: Mapped[str] = mapped_column(String(36), ForeignKey("journeys.id", ondelete="CASCADE"), index=True)
    stage: Mapped[str] = mapped_column(String(40))
    source: Mapped[str] = mapped_column(String(30))
    suppressed: Mapped[bool] = mapped_column(Boolean)
    reason_code: Mapped[str | None] = mapped_column(String(120), nullable=True)
    rule_version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class AuditRecord(Base):
    __tablename__ = "audit_events"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    action: Mapped[str] = mapped_column(String(48), nullable=False)
    resource_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    # Deliberately do not log route contents, transcript, GPS, or bearer tokens.


def make_engine(database_url: str) -> Engine:
    kwargs = {"pool_pre_ping": True}
    if database_url.startswith("sqlite"):
        kwargs["connect_args"] = {"check_same_thread": False}
    engine = create_engine(database_url, **kwargs)
    if database_url.startswith("sqlite"):
        @event.listens_for(engine, "connect")
        def _sqlite_foreign_keys(dbapi_conn, _):
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()
    return engine


def session_factory(engine: Engine):
    return sessionmaker(engine, expire_on_commit=False, autoflush=False)
