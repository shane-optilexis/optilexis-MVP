"""multiuser foundation

Revision ID: 0001_multiuser_foundation
Revises:
"""
from alembic import op
import sqlalchemy as sa

revision = "0001_multiuser_foundation"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("users",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("issuer", sa.String(255), nullable=False),
        sa.Column("subject", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ux_users_issuer_subject", "users", ["issuer", "subject"], unique=True)
    op.create_table("journeys",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("destination", sa.String(160), nullable=False),
        sa.Column("language", sa.String(8), nullable=False),
        sa.Column("mode", sa.String(10), nullable=False),
        sa.Column("navigation_mode", sa.String(32), nullable=False),
        sa.Column("stage", sa.String(40), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("closed_at", sa.DateTime(timezone=True)))
    op.create_index("ix_journeys_user_id", "journeys", ["user_id"])
    op.create_table("consents",
        sa.Column("journey_id", sa.String(36), sa.ForeignKey("journeys.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("location", sa.Boolean(), nullable=False),
        sa.Column("microphone", sa.Boolean(), nullable=False),
        sa.Column("camera", sa.Boolean(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False))
    op.create_table("routes",
        sa.Column("journey_id", sa.String(36), sa.ForeignKey("journeys.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("provider", sa.String(35), nullable=False),
        sa.Column("real_route_started", sa.Boolean(), nullable=False))
    op.create_table("journey_sessions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("journey_id", sa.String(36), sa.ForeignKey("journeys.id", ondelete="CASCADE"), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True)))
    op.create_index("ix_journey_sessions_journey_id", "journey_sessions", ["journey_id"])
    op.create_table("recommendation_events",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("journey_id", sa.String(36), sa.ForeignKey("journeys.id", ondelete="CASCADE"), nullable=False),
        sa.Column("stage", sa.String(40), nullable=False),
        sa.Column("source", sa.String(30), nullable=False),
        sa.Column("suppressed", sa.Boolean(), nullable=False),
        sa.Column("reason_code", sa.String(120)),
        sa.Column("rule_version", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_recommendation_events_journey_id", "recommendation_events", ["journey_id"])
    op.create_table("audit_events",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("action", sa.String(48), nullable=False),
        sa.Column("resource_id", sa.String(36)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_audit_events_user_id", "audit_events", ["user_id"])


def downgrade():
    op.drop_index("ix_audit_events_user_id", table_name="audit_events")
    op.drop_table("audit_events")
    op.drop_index("ix_recommendation_events_journey_id", table_name="recommendation_events")
    op.drop_table("recommendation_events")
    op.drop_index("ix_journey_sessions_journey_id", table_name="journey_sessions")
    op.drop_table("journey_sessions")
    op.drop_table("routes")
    op.drop_table("consents")
    op.drop_index("ix_journeys_user_id", table_name="journeys")
    op.drop_table("journeys")
    op.drop_index("ux_users_issuer_subject", table_name="users")
    op.drop_table("users")
