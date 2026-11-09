"""Typed domain storage. SQLite foreign keys + WAL; tenant predicates live in service helpers."""

import os, uuid
from datetime import datetime, timezone
from sqlalchemy import (
    create_engine,
    String,
    Integer,
    Float,
    Boolean,
    JSON,
    ForeignKey,
    UniqueConstraint,
    event,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker
from dotenv import load_dotenv

load_dotenv()


def uid():
    return str(uuid.uuid4())


def utc():
    return datetime.now(timezone.utc).isoformat()


class Base(DeclarativeBase):
    pass


class Tenant(Base):
    __tablename__ = "tenants"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str]
    settings: Mapped[dict] = mapped_column(JSON, default=dict)
    clock: Mapped[str]


class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    email: Mapped[str] = mapped_column(unique=True)
    name: Mapped[str]
    password_hash: Mapped[str]


class Membership(Base):
    __tablename__ = "memberships"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    role: Mapped[str]
    __table_args__ = (UniqueConstraint("tenant_id", "user_id"),)


class Session(Base):
    __tablename__ = "sessions"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    csrf: Mapped[str]
    expires: Mapped[str]


class Rep(Base):
    __tablename__ = "sales_reps"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    name: Mapped[str]
    skills: Mapped[list] = mapped_column(JSON)
    capacity: Mapped[int] = mapped_column(default=12)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    shift_start: Mapped[int] = mapped_column(default=9)
    shift_end: Mapped[int] = mapped_column(default=18)
    response: Mapped[float] = mapped_column(default=0.8)


class Campaign(Base):
    __tablename__ = "campaigns"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), index=True)
    name: Mapped[str]
    source: Mapped[str]


class Lead(Base):
    __tablename__ = "leads"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), index=True)
    external_id: Mapped[str]
    name: Mapped[str]
    contact: Mapped[str]
    email: Mapped[str] = mapped_column(default="")
    source: Mapped[str]
    campaign_id: Mapped[str | None] = mapped_column(
        ForeignKey("campaigns.id"), nullable=True
    )
    city: Mapped[str]
    interest: Mapped[str]
    inquiry: Mapped[str]
    budget: Mapped[int | None] = mapped_column(nullable=True)
    urgency: Mapped[str] = mapped_column(default="this_week")
    stage: Mapped[str] = mapped_column(default="new", index=True)
    owner_id: Mapped[str | None] = mapped_column(
        ForeignKey("sales_reps.id"), nullable=True
    )
    score: Mapped[float] = mapped_column(default=0)
    consent: Mapped[str] = mapped_column(default="unknown")
    consent_source: Mapped[str] = mapped_column(default="manual")
    consent_at: Mapped[str | None] = mapped_column(nullable=True)
    opt_out_at: Mapped[str | None] = mapped_column(nullable=True)
    created_at: Mapped[str]
    updated_at: Mapped[str]
    first_response_at: Mapped[str | None] = mapped_column(nullable=True)
    responded_at: Mapped[str | None] = mapped_column(nullable=True)
    appointment_at: Mapped[str | None] = mapped_column(nullable=True)
    outcome_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    deal_value: Mapped[int] = mapped_column(default=0)
    deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    is_synthetic: Mapped[bool] = mapped_column(Boolean, default=True)
    __table_args__ = (
        UniqueConstraint("tenant_id", "external_id"),
        UniqueConstraint("tenant_id", "contact"),
    )


class Event(Base):
    __tablename__ = "lead_events"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), index=True)
    lead_id: Mapped[str] = mapped_column(ForeignKey("leads.id"), index=True)
    kind: Mapped[str]
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    actor: Mapped[str] = mapped_column(default="system")
    origin: Mapped[str] = mapped_column(default="simulation")
    correlation_id: Mapped[str] = mapped_column(default=uid)
    created_at: Mapped[str]


class Recommendation(Base):
    __tablename__ = "recommendations"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), index=True)
    lead_id: Mapped[str | None] = mapped_column(ForeignKey("leads.id"), nullable=True)
    agent: Mapped[str]
    action: Mapped[str]
    inputs: Mapped[dict] = mapped_column(JSON)
    alternatives: Mapped[list] = mapped_column(JSON, default=list)
    explanation: Mapped[dict] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(default="recommended")
    policy_version: Mapped[str] = mapped_column(default="LP-1")
    created_at: Mapped[str]


class Assignment(Base):
    __tablename__ = "assignments"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), index=True)
    lead_id: Mapped[str] = mapped_column(ForeignKey("leads.id"))
    rep_id: Mapped[str] = mapped_column(ForeignKey("sales_reps.id"))
    utility: Mapped[float]
    status: Mapped[str] = mapped_column(default="active")
    approved_by: Mapped[str]
    policy_version: Mapped[str] = mapped_column(default="LP-1")
    created_at: Mapped[str]


class Task(Base):
    __tablename__ = "tasks"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), index=True)
    lead_id: Mapped[str] = mapped_column(ForeignKey("leads.id"), index=True)
    assigned_to: Mapped[str | None] = mapped_column(
        ForeignKey("sales_reps.id"), nullable=True
    )
    kind: Mapped[str] = mapped_column(default="first_response")
    due_at: Mapped[str]
    status: Mapped[str] = mapped_column(default="pending")
    completed_at: Mapped[str | None] = mapped_column(nullable=True)
    created_at: Mapped[str]


class Communication(Base):
    __tablename__ = "communications"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), index=True)
    lead_id: Mapped[str] = mapped_column(ForeignKey("leads.id"))
    direction: Mapped[str]
    channel: Mapped[str]
    body: Mapped[str]
    status: Mapped[str]
    consent_snapshot: Mapped[str]
    simulated: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[str]


class Job(Base):
    __tablename__ = "jobs"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), index=True)
    lead_id: Mapped[str] = mapped_column(ForeignKey("leads.id"))
    task_id: Mapped[str | None] = mapped_column(ForeignKey("tasks.id"), nullable=True)
    correlation_id: Mapped[str] = mapped_column(default=uid)
    created_at: Mapped[str]
    due_at: Mapped[str]
    status: Mapped[str] = mapped_column(default="queued")
    retry_count: Mapped[int] = mapped_column(default=0)
    locked_until: Mapped[str | None] = mapped_column(nullable=True)
    last_error: Mapped[str | None] = mapped_column(nullable=True)
    payload: Mapped[dict] = mapped_column(JSON)


class Audit(Base):
    __tablename__ = "audit_events"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), index=True)
    actor: Mapped[str]
    action: Mapped[str]
    target_id: Mapped[str]
    reason: Mapped[str]
    before: Mapped[dict] = mapped_column(JSON, default=dict)
    after: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[str]


class Idempotency(Base):
    __tablename__ = "idempotency"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), index=True)
    fingerprint: Mapped[str]
    response: Mapped[dict] = mapped_column(JSON)


URL = os.getenv("DATABASE_URL", "sqlite:///./demo.db")
engine = create_engine(
    URL,
    connect_args=(
        {"check_same_thread": False, "timeout": 30} if URL.startswith("sqlite") else {}
    ),
)


@event.listens_for(engine, "connect")
def sqlite_config(c, _):
    if URL.startswith("sqlite"):
        c.execute("PRAGMA foreign_keys=ON")
        c.execute("PRAGMA journal_mode=WAL")


SessionLocal = sessionmaker(engine, expire_on_commit=False)


def serialize(row):
    return {c.name: getattr(row, c.name) for c in row.__table__.columns}
