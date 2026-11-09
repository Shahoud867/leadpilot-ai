import asyncio, csv, hashlib, io, json, os, secrets, time
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from contextlib import asynccontextmanager
from typing import Literal
from fastapi import FastAPI, Depends, HTTPException, Request, Response, Query
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select, or_, func
from .db import *
from .auth import current, db_session, permit, ph
from .domain import *
from .agents import *
from .service import *
from .seed import seed, stable


@asynccontextmanager
async def lifespan(app):
    with SessionLocal() as db:
        if not db.scalar(select(Tenant)):
            seed(db, seed_value=int(os.getenv("SEED", "20261108")))
    yield


app = FastAPI(
    title="LeadPilot AI · local simulated demo", version="1.0.0", lifespan=lifespan
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv(
        "CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
    ).split(","),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH"],
    allow_headers=["Content-Type", "X-CSRF-Token", "Idempotency-Key", "X-Request-ID"],
)
write_lock = asyncio.Lock()
attempts = defaultdict(list)


@app.middleware("http")
async def guard(request, call_next):
    """Commit domain changes and idempotency response in one SQLite transaction."""
    rid = request.headers.get("X-Request-ID", uid())[:128]
    mutating = request.method in ("POST", "PATCH", "DELETE")
    body = await request.body() if mutating else b""
    if len(body) > 1024 * 1024:
        return JSONResponse({"detail": "Upload exceeds 1 MiB"}, 413)

    async def invoke():
        with SessionLocal() as db:
            request.state.db = db
            key = request.headers.get("Idempotency-Key")
            cache_id = tid = fp = None
            if key and mutating and "/auth/" not in request.url.path:
                s = db.get(
                    Session,
                    hashlib.sha256(
                        request.cookies.get("lp_session", "").encode()
                    ).hexdigest(),
                )
                if (
                    s
                    and s.expires > utc()
                    and secrets.compare_digest(
                        request.headers.get("X-CSRF-Token", ""), s.csrf
                    )
                ):
                    membership = db.scalar(
                        select(Membership).where(Membership.user_id == s.user_id)
                    )
                    if membership:
                        tid = membership.tenant_id
                        fp = hashlib.sha256(
                            request.method.encode()
                            + str(request.url).encode()
                            + body
                            + s.user_id.encode()
                            + membership.role.encode()
                        ).hexdigest()
                        cache_id = hashlib.sha256((tid + key).encode()).hexdigest()
                        cached = db.get(Idempotency, cache_id)
                        if cached:
                            if cached.fingerprint != fp:
                                return JSONResponse(
                                    {
                                        "detail": "Idempotency key reused with different request or role"
                                    },
                                    409,
                                )
                            return JSONResponse(
                                cached.response, headers={"X-Idempotent-Replay": "true"}
                            )
            try:
                result = await call_next(request)
                if mutating and 200 <= result.status_code < 300:
                    content = b""
                    async for chunk in result.body_iterator:
                        content += chunk
                    if cache_id:
                        payload = json.loads(content)
                        db.add(
                            Idempotency(
                                id=cache_id,
                                tenant_id=tid,
                                fingerprint=fp,
                                response=payload,
                            )
                        )
                    db.commit()
                    result = Response(
                        content,
                        status_code=result.status_code,
                        headers=dict(result.headers),
                        media_type=result.media_type,
                    )
                elif mutating:
                    db.rollback()
                return result
            except Exception:
                db.rollback()
                raise

    if mutating:
        async with write_lock:
            response = await invoke()
    else:
        response = await invoke()
    response.headers.update(
        {
            "X-Request-ID": rid,
            "X-Content-Type-Options": "nosniff",
            "Referrer-Policy": "same-origin",
            "X-Frame-Options": "DENY",
            "Cache-Control": "no-store",
        }
    )
    return response


class Login(BaseModel):
    email: str = Field(max_length=150)
    password: str = Field(max_length=200)


@app.post("/api/v1/auth/login")
def login(data: Login, request: Request, response: Response, db=Depends(db_session)):
    key = request.client.host
    recent = [x for x in attempts[key] if x > time.time() - 60]
    attempts[key] = recent
    if len(recent) >= 15:
        raise HTTPException(429, "Too many attempts; wait one minute")
    user = db.scalar(select(User).where(User.email == data.email.lower()))
    try:
        valid = bool(user and ph.verify(user.password_hash, data.password))
    except Exception:
        valid = False
    if not valid:
        attempts[key].append(time.time())
        raise HTTPException(401, "Email or password is incorrect")
    token = secrets.token_urlsafe(40)
    csrf = secrets.token_urlsafe(32)
    db.add(
        Session(
            id=hashlib.sha256(token.encode()).hexdigest(),
            user_id=user.id,
            csrf=csrf,
            expires=(datetime.now(timezone.utc) + timedelta(hours=8)).isoformat(),
        )
    )
    response.set_cookie(
        "lp_session",
        token,
        httponly=True,
        samesite="strict",
        secure=os.getenv("COOKIE_SECURE", "false") == "true",
        max_age=28800,
    )
    return {"csrf": csrf}


@app.get("/api/v1/auth/me")
def me(user=Depends(current), db=Depends(db_session)):
    return {**user, "tenant": serialize(db.get(Tenant, user["tenant_id"]))}


@app.post("/api/v1/auth/logout")
def logout(
    request: Request, response: Response, user=Depends(current), db=Depends(db_session)
):
    s = db.get(
        Session, hashlib.sha256(request.cookies["lp_session"].encode()).hexdigest()
    )
    db.delete(s)
    response.delete_cookie("lp_session")
    return {"ok": True}


@app.get("/api/v1/health")
def health():
    return {"status": "ok", "simulated_externals": True}


class LeadIn(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    contact: str = Field(pattern=r"(?i)^SYN-[A-Z0-9-]{3,60}$")
    email: str = Field(default="", max_length=150)
    source: Literal["WhatsApp", "Instagram", "Website", "Walk-in"] = "Website"
    city: str = Field(default="Islamabad", min_length=2, max_length=80)
    interest: str = Field(min_length=2, max_length=100)
    inquiry: str = Field(min_length=5, max_length=3000)
    budget: int | None = Field(default=None, ge=0, le=2000000000)
    urgency: Literal["today", "this_week", "this_month"] = "this_week"
    consent: Literal["granted", "unknown", "opted_out"] = "unknown"
    campaign_id: str | None = None
    external_id: str | None = Field(default=None, max_length=100)

    @field_validator("email")
    @classmethod
    def fake_email(cls, v):
        v = v.strip().lower()
        if v and not v.endswith(".example"):
            raise ValueError("Use a synthetic .example email for this demo")
        return v


@app.post("/api/v1/leads")
def create_lead(data: LeadIn, user=Depends(current), db=Depends(db_session)):
    permit(user, ("owner", "manager"))
    return capture(db, user["tenant_id"], data.model_dump(), user["id"])


@app.get("/api/v1/leads")
def leads(
    q: str = "",
    stage: str = "",
    source: str = "",
    owner: str = "",
    sort: str = "created_at",
    page: int = Query(1, ge=1),
    page_size: int = Query(30, ge=1, le=100),
    user=Depends(current),
    db=Depends(db_session),
):
    stmt = select(Lead).where(
        Lead.tenant_id == user["tenant_id"], Lead.deleted == False
    )
    if user["role"] == "operator":
        stmt = stmt.where(Lead.owner_id == user["rep_id"])
    if q:
        stmt = stmt.where(
            or_(
                Lead.name.ilike("%" + q[:150] + "%"),
                Lead.interest.ilike("%" + q[:150] + "%"),
                Lead.contact.ilike("%" + q[:150] + "%"),
            )
        )
    if stage:
        stmt = stmt.where(Lead.stage == stage)
    if source:
        stmt = stmt.where(Lead.source == source)
    if owner:
        stmt = stmt.where(Lead.owner_id == owner)
    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    order = {
        "score": Lead.score.desc(),
        "name": Lead.name.asc(),
        "created_at": Lead.created_at.desc(),
    }.get(sort, Lead.created_at.desc())
    data = db.scalars(
        stmt.order_by(order, Lead.id)
        .offset((max(1, page) - 1) * min(100, page_size))
        .limit(max(1, min(100, page_size)))
    ).all()
    return {
        "items": [serialize(l) for l in data],
        "total": total,
        "page": page,
        "page_size": min(100, page_size),
    }


@app.get("/api/v1/leads/export")
def export(user=Depends(current), db=Depends(db_session)):
    out = io.StringIO()
    w = csv.writer(out)
    w.writerow(["SIMULATED DATA · LP-1"])
    w.writerow(
        [
            "id",
            "name",
            "contact",
            "source",
            "interest",
            "stage",
            "score",
            "deal_value_pkr",
        ]
    )

    def safe(v):
        s = str(v)
        return (
            "'" + s
            if (
                s.lstrip().startswith(("=", "+", "-", "@"))
                or s.startswith(("\t", "\r", "\n"))
            )
            else s
        )

    for l in rows(db, Lead, user["tenant_id"]):
        if not l.deleted and (
            user["role"] != "operator" or l.owner_id == user["rep_id"]
        ):
            w.writerow(
                [
                    safe(getattr(l, k))
                    for k in [
                        "id",
                        "name",
                        "contact",
                        "source",
                        "interest",
                        "stage",
                        "score",
                        "deal_value",
                    ]
                ]
            )
    return Response(
        out.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=leadpilot-simulated.csv"},
    )


class ImportIn(BaseModel):
    csv_text: str = Field(max_length=900000)
    dry_run: bool = True


@app.post("/api/v1/leads/import")
def import_csv(data: ImportIn, user=Depends(current), db=Depends(db_session)):
    permit(user, ("owner", "manager"))
    raw = list(csv.DictReader(io.StringIO(data.csv_text)))
    if len(raw) > 1000:
        raise HTTPException(422, "Maximum 1,000 rows per import")
    parsed = []
    errors = []
    for i, row in enumerate(raw):
        try:
            if row.get("budget") == "":
                row["budget"] = None
            parsed.append(LeadIn(**row).model_dump())
        except Exception as e:
            errors.append({"row": i + 2, "error": str(e)[:350]})
    if errors:
        return {
            "valid": False,
            "errors": errors,
            "rows": len(raw),
            "created": 0,
            "duplicates": 0,
        }
    seen = {l.contact for l in rows(db, Lead, user["tenant_id"])}
    known = rows(db, Lead, user["tenant_id"])
    seen_emails = {l.email for l in known if l.email}
    seen_external = {l.external_id for l in known}
    created = duplicates = 0
    ids = []
    for row in parsed:
        dup = (
            row["contact"].upper() in seen
            or bool(row.get("email") and row["email"] in seen_emails)
            or bool(row.get("external_id") and row["external_id"] in seen_external)
        )
        if data.dry_run:
            duplicates += int(dup)
            created += int(not dup)
            seen.add(row["contact"].upper())
            if row.get("email"):
                seen_emails.add(row["email"])
            if row.get("external_id"):
                seen_external.add(row["external_id"])
        else:
            result = capture(db, user["tenant_id"], row, user["id"], auto_assign=False)
            duplicates += int(result["duplicate"])
            created += int(not result["duplicate"])
            if not result["duplicate"]:
                ids.append(result["lead"]["id"])
    if ids:
        commit_allocation(
            db,
            user["tenant_id"],
            allocation_preview(
                db, user["tenant_id"], [db.get(Lead, lid) for lid in ids[:100]]
            ),
            user["id"],
        )
    return {
        "valid": True,
        "rows": len(raw),
        "created": created,
        "duplicates": duplicates,
        "dry_run": data.dry_run,
        "errors": [],
    }


@app.get("/api/v1/leads/{lid}")
def detail(lid: str, user=Depends(current), db=Depends(db_session)):
    l = get_lead(db, user, lid)

    def child(model):
        return [
            serialize(x)
            for x in db.scalars(
                select(model).where(
                    model.tenant_id == user["tenant_id"], model.lead_id == lid
                )
            )
        ]

    return {
        "lead": serialize(l),
        "events": sorted(child(Event), key=lambda e: (e["created_at"], e["id"])),
        "recommendations": child(Recommendation),
        "tasks": child(Task),
        "messages": child(Communication),
        "assignments": child(Assignment),
    }


class EditIn(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    interest: str | None = Field(default=None, min_length=2, max_length=100)
    budget: int | None = Field(default=None, ge=0, le=2000000000)
    urgency: Literal["today", "this_week", "this_month"] | None = None
    consent: Literal["granted", "unknown", "opted_out"] | None = None
    reason: str = Field(min_length=3, max_length=500)


@app.patch("/api/v1/leads/{lid}")
def edit(lid: str, data: EditIn, user=Depends(current), db=Depends(db_session)):
    permit(user)
    l = get_lead(db, user, lid)
    before = serialize(l)
    for k, v in data.model_dump(exclude_unset=True).items():
        if k != "reason":
            setattr(l, k, v)
    if data.consent == "opted_out":
        l.opt_out_at = now(db, l.tenant_id)
    if data.consent == "granted":
        l.consent_at = now(db, l.tenant_id)
        l.consent_source = "manual_approved"
    emit(db, l, "lead_edited", {"reason": data.reason}, user["id"])
    qualify(db, l)
    audit(
        db,
        l.tenant_id,
        user["id"],
        "lead_edited",
        lid,
        data.reason,
        before,
        serialize(l),
    )
    return serialize(l)


@app.post("/api/v1/leads/{lid}/qualify")
def qualify_lead(lid: str, user=Depends(current), db=Depends(db_session)):
    permit(user)
    return serialize(qualify(db, get_lead(db, user, lid)))


class TransitionIn(BaseModel):
    stage: Literal[
        "new",
        "assigned",
        "contacted",
        "qualified",
        "appointment",
        "won",
        "lost",
        "dormant",
        "reopened",
        "archived",
    ]
    reason: str = Field(default="", max_length=500)
    verified: bool = False
    appointment_at: str | None = None
    value: int = Field(default=0, ge=0, le=2000000000)


@app.post("/api/v1/leads/{lid}/transition")
def move(lid: str, data: TransitionIn, user=Depends(current), db=Depends(db_session)):
    permit(user)
    l = get_lead(db, user, lid)
    if l.stage == "archived":
        permit(user, ("owner",))
    if data.appointment_at:
        try:
            if dt(data.appointment_at).tzinfo is None:
                raise ValueError()
        except ValueError:
            raise HTTPException(422, "Timezone-aware ISO appointment required")
    transition(
        db,
        l,
        data.stage,
        user["id"],
        data.reason,
        data.verified,
        data.appointment_at,
        data.value,
    )
    analytics_trace(db, l)
    return serialize(l)


class ReplyIn(BaseModel):
    body: str = Field(
        default="Simulated: I would like to book a consultation.",
        min_length=3,
        max_length=2000,
    )


@app.post("/api/v1/leads/{lid}/reply")
def customer_reply(
    lid: str, data: ReplyIn, user=Depends(current), db=Depends(db_session)
):
    permit(user)
    l = get_lead(db, user, lid)
    if l.stage in TERMINAL:
        raise HTTPException(422, "Closed lead cannot receive a workflow reply")
    reply(db, l, user["id"], data.body)
    return serialize(l)


class OverrideIn(BaseModel):
    rep_id: str
    reason: str = Field(min_length=3, max_length=500)


@app.post("/api/v1/leads/{lid}/override")
def override(lid: str, data: OverrideIn, user=Depends(current), db=Depends(db_session)):
    permit(user, ("owner", "manager"))
    l = get_lead(db, user, lid)
    reassign(db, user, l, data.rep_id, data.reason)
    return serialize(l)


class DeleteIn(BaseModel):
    reason: str = Field(min_length=5, max_length=500)


@app.post("/api/v1/leads/{lid}/delete")
def redact(lid: str, data: DeleteIn, user=Depends(current), db=Depends(db_session)):
    permit(user, ("owner",))
    l = get_lead(db, user, lid)
    l.deleted = True
    l.name = "Redacted synthetic contact"
    l.email = ""
    l.contact = "SYN-REDACTED-" + l.id
    l.inquiry = "Redacted"
    l.consent = "opted_out"
    for c in db.scalars(
        select(Communication).where(
            Communication.tenant_id == l.tenant_id, Communication.lead_id == l.id
        )
    ):
        c.body = "Redacted"
    for e in db.scalars(
        select(Event).where(Event.tenant_id == l.tenant_id, Event.lead_id == l.id)
    ):
        e.payload = {"redacted": True}
    for a in db.scalars(
        select(Audit).where(Audit.tenant_id == l.tenant_id, Audit.target_id == l.id)
    ):
        a.before = {}
        a.after = {}
    for t in db.scalars(
        select(Task).where(
            Task.tenant_id == l.tenant_id,
            Task.lead_id == l.id,
            Task.status == "pending",
        )
    ):
        t.status = "canceled"
    for j in db.scalars(
        select(Job).where(Job.tenant_id == l.tenant_id, Job.lead_id == l.id)
    ):
        j.payload = {"body": "Redacted"}
        j.status = "suppressed"
    for r in db.scalars(
        select(Recommendation).where(
            Recommendation.tenant_id == l.tenant_id, Recommendation.lead_id == l.id
        )
    ):
        r.inputs = {}
        r.explanation = {"note": "Contact redacted"}
    for cached in rows(db, Idempotency, l.tenant_id):
        if lid in json.dumps(cached.response):
            db.delete(cached)
    audit(db, l.tenant_id, user["id"], "contact_redacted", lid, data.reason)
    return {"ok": True}


class IDs(BaseModel):
    lead_ids: list[str] = Field(default=[], max_length=100)


@app.post("/api/v1/assignments/preview")
def preview(data: IDs, user=Depends(current), db=Depends(db_session)):
    permit(user, ("owner", "manager"))
    ls = (
        [get_lead(db, user, x) for x in data.lead_ids]
        if data.lead_ids
        else list(
            db.scalars(
                select(Lead)
                .where(
                    Lead.tenant_id == user["tenant_id"],
                    Lead.owner_id == None,
                    Lead.deleted == False,
                    Lead.stage.notin_(TERMINAL),
                )
                .order_by(Lead.score.desc(), Lead.id)
                .limit(100)
            )
        )
    )
    return allocation_preview(db, user["tenant_id"], ls)


@app.post("/api/v1/assignments/commit")
def commit(data: IDs, user=Depends(current), db=Depends(db_session)):
    permit(user, ("owner", "manager"))
    p = preview(data, user, db)
    commit_allocation(db, user["tenant_id"], p, user["id"])
    return p


@app.get("/api/v1/tasks")
def tasks(user=Depends(current), db=Depends(db_session)):
    result = []
    for t in rows(db, Task, user["tenant_id"]):
        l = db.get(Lead, t.lead_id)
        if l.deleted or (user["role"] == "operator" and l.owner_id != user["rep_id"]):
            continue
        if t.status == "pending":
            result.append(
                {
                    **serialize(t),
                    "lead_name": l.name,
                    "interest": l.interest,
                    "consent": l.consent,
                    "overdue": t.due_at < now(db, l.tenant_id),
                }
            )
    return sorted(result, key=lambda t: t["due_at"])


class TaskAction(BaseModel):
    action: Literal["send", "complete", "snooze"] = "send"
    body: str = Field(
        default="Simulated: Assalam-o-Alaikum! Thank you for your inquiry. May we arrange a consultation?",
        min_length=3,
        max_length=2000,
    )
    minutes: int = Field(default=60, ge=1, le=10080)
    inject_failure: bool = False


@app.post("/api/v1/tasks/{task_id}/action")
def task_action(
    task_id: str, data: TaskAction, user=Depends(current), db=Depends(db_session)
):
    permit(user)
    t = db.scalar(
        select(Task).where(Task.id == task_id, Task.tenant_id == user["tenant_id"])
    )
    if not t:
        raise HTTPException(404, "Task not found")
    l = get_lead(db, user, t.lead_id)
    if t.status != "pending":
        raise HTTPException(409, "Task is no longer pending")
    if data.action == "send":
        j = enqueue(db, l, t, data.body, data.inject_failure, user["id"])
        return {
            "job": serialize(j),
            "message": "Approved for simulation; process queue to deliver.",
        }
    if data.action == "complete":
        t.status = "completed"
        t.completed_at = now(db, l.tenant_id)
    else:
        t.due_at = plus(now(db, l.tenant_id), data.minutes)
    emit(db, l, "task_" + data.action, {"task_id": t.id}, user["id"])
    return serialize(t)


@app.post("/api/v1/jobs/process")
def run_jobs(user=Depends(current), db=Depends(db_session)):
    permit(user, ("owner", "manager"))
    return {"results": process_jobs(db, user["tenant_id"])}


@app.get("/api/v1/jobs")
def jobs(user=Depends(current), db=Depends(db_session)):
    return [
        serialize(j)
        for j in rows(db, Job, user["tenant_id"])
        if user["role"] != "operator"
        or db.get(Lead, j.lead_id).owner_id == user["rep_id"]
    ]


@app.get("/api/v1/analytics")
def metrics(
    days: int = 30, source: str = "", user=Depends(current), db=Depends(db_session)
):
    return analytics(db, user, max(0, min(days, 365)), source)


@app.get("/api/v1/recommendations")
def recs(agent: str = "", user=Depends(current), db=Depends(db_session)):
    stmt = (
        select(Recommendation)
        .join(Lead, Lead.id == Recommendation.lead_id)
        .where(
            Recommendation.tenant_id == user["tenant_id"],
            Lead.tenant_id == user["tenant_id"],
            Lead.deleted == False,
        )
    )
    if agent:
        stmt = stmt.where(Recommendation.agent == agent)
    if user["role"] == "operator":
        stmt = stmt.where(Lead.owner_id == user["rep_id"])
    return [
        serialize(r)
        for r in db.scalars(
            stmt.order_by(Recommendation.created_at.desc(), Recommendation.id).limit(
                250
            )
        )
    ]


@app.post("/api/v1/recovery/scan")
def scan(user=Depends(current), db=Depends(db_session)):
    permit(user, ("owner", "manager"))
    return {"recommendations": recovery(db, user["tenant_id"])}


class DecisionIn(BaseModel):
    action: Literal["approve", "dismiss"]
    reason: str = Field(min_length=3, max_length=500)


@app.post("/api/v1/recommendations/{rid}/decision")
def decision(rid: str, data: DecisionIn, user=Depends(current), db=Depends(db_session)):
    permit(user, ("owner", "manager"))
    r = db.scalar(
        select(Recommendation).where(
            Recommendation.id == rid, Recommendation.tenant_id == user["tenant_id"]
        )
    )
    if not r:
        raise HTTPException(404, "Recommendation not found")
    if r.status != "recommended":
        raise HTTPException(409, "Already resolved")
    r.status = "approved" if data.action == "approve" else "dismissed"
    audit(
        db,
        user["tenant_id"],
        user["id"],
        "recommendation_" + data.action,
        rid,
        data.reason,
    )
    return serialize(r)


@app.get("/api/v1/team")
def team(user=Depends(current), db=Depends(db_session)):
    return analytics(db, user, 0)["team"]


class RepEdit(BaseModel):
    capacity: int = Field(ge=1, le=200)
    active: bool
    shift_start: int = Field(ge=0, le=23)
    shift_end: int = Field(ge=1, le=24)
    skills: list[str] = Field(min_length=1, max_length=20)


@app.patch("/api/v1/team/{rep_id}")
def edit_rep(rep_id: str, data: RepEdit, user=Depends(current), db=Depends(db_session)):
    permit(user, ("owner", "manager"))
    r = db.scalar(
        select(Rep).where(Rep.id == rep_id, Rep.tenant_id == user["tenant_id"])
    )
    if not r:
        raise HTTPException(404, "Representative not found")
    if data.shift_end <= data.shift_start:
        raise HTTPException(422, "Shift end must follow start")
    before = serialize(r)
    for k, v in data.model_dump().items():
        setattr(r, k, v)
    audit(
        db,
        user["tenant_id"],
        user["id"],
        "team_updated",
        rep_id,
        "Capacity / availability configuration",
        before,
        serialize(r),
    )
    return serialize(r)


@app.get("/api/v1/members")
def members(user=Depends(current), db=Depends(db_session)):
    permit(user, ("owner", "manager"))
    return [
        {
            "id": m.id,
            "role": m.role,
            "name": db.get(User, m.user_id).name,
            "email": db.get(User, m.user_id).email,
        }
        for m in rows(db, Membership, user["tenant_id"])
    ]


class RoleIn(BaseModel):
    role: Literal["manager", "operator", "viewer"]


@app.patch("/api/v1/members/{mid}")
def role(mid: str, data: RoleIn, user=Depends(current), db=Depends(db_session)):
    permit(user, ("owner",))
    m = db.scalar(
        select(Membership).where(
            Membership.id == mid, Membership.tenant_id == user["tenant_id"]
        )
    )
    if not m:
        raise HTTPException(404, "Member not found")
    if m.role == "owner":
        raise HTTPException(422, "Demo owner role is protected")
    if data.role == "operator" and not db.scalar(
        select(Rep).where(Rep.user_id == m.user_id, Rep.tenant_id == m.tenant_id)
    ):
        raise HTTPException(
            422, "Only a configured representative can become an operator"
        )
    before = m.role
    m.role = data.role
    audit(
        db,
        m.tenant_id,
        user["id"],
        "role_updated",
        mid,
        "Owner changed membership",
        {"role": before},
        {"role": m.role},
    )
    return {"role": m.role}


@app.get("/api/v1/settings")
def settings(user=Depends(current), db=Depends(db_session)):
    return serialize(db.get(Tenant, user["tenant_id"]))


class SettingsIn(BaseModel):
    sla_minutes: int = Field(ge=1, le=1440)
    retention_days: int = Field(ge=7, le=730)


@app.patch("/api/v1/settings")
def update_settings(data: SettingsIn, user=Depends(current), db=Depends(db_session)):
    permit(user, ("owner",))
    t = db.get(Tenant, user["tenant_id"])
    before = t.settings
    t.settings = {**t.settings, **data.model_dump()}
    audit(
        db,
        t.id,
        user["id"],
        "settings_updated",
        t.id,
        "Owner configuration",
        before,
        t.settings,
    )
    return serialize(t)


@app.get("/api/v1/campaigns")
def campaigns(user=Depends(current), db=Depends(db_session)):
    return [serialize(c) for c in rows(db, Campaign, user["tenant_id"])]


@app.get("/api/v1/audit")
def audits(user=Depends(current), db=Depends(db_session)):
    permit(user, ("owner", "manager", "viewer"))
    return [
        serialize(a)
        for a in db.scalars(
            select(Audit)
            .where(Audit.tenant_id == user["tenant_id"])
            .order_by(Audit.created_at.desc(), Audit.id)
            .limit(300)
        )
    ]


class ClockIn(BaseModel):
    minutes: int = Field(ge=1, le=10080)


@app.post("/api/v1/demo/clock/advance")
def advance(data: ClockIn, user=Depends(current), db=Depends(db_session)):
    permit(user, ("owner", "manager"))
    t = db.get(Tenant, user["tenant_id"])
    t.clock = plus(t.clock, data.minutes)
    found = recovery(db, t.id)
    jobs = process_jobs(db, t.id)
    audit(db, t.id, user["id"], "clock_advanced", t.id, after={"minutes": data.minutes})
    return {"clock": t.clock, "escalations": len(found), "jobs": jobs}


class ResetIn(BaseModel):
    confirmation: Literal["RESET SYNTHETIC DATA"]


@app.post("/api/v1/demo/reset")
def reset(data: ResetIn, user=Depends(current), db=Depends(db_session)):
    permit(user, ("owner",))
    seed(
        db,
        seed_value=db.get(Tenant, user["tenant_id"]).settings.get("seed", 20261108),
        reset=True,
        tenant_only=user["tenant_id"],
        commit=False,
    )
    audit(
        db,
        user["tenant_id"],
        user["id"],
        "demo_reset",
        user["tenant_id"],
        "Explicit reset confirmation",
    )
    return {"ok": True, "clock": now(db, user["tenant_id"])}


SCENARIOS = {
    "inquiry",
    "high_value",
    "sla",
    "capacity",
    "appointment",
    "override",
    "conversion",
    "burst",
    "opt_out",
    "retry",
}


@app.post("/api/v1/demo/scenarios/{key}/run")
def scenario(key: str, user=Depends(current), db=Depends(db_session)):
    permit(user, ("owner", "manager"))
    if key not in SCENARIOS:
        raise HTTPException(404, "Scenario not found")
    tid = user["tenant_id"]
    before = analytics(db, user, 0)
    created = []
    comparison = None

    def inject(i=0, assign=True, consent="granted"):
        data = LeadIn(
            name=(
                "Ayesha · Missed admission"
                if key == "sla"
                else f'{NAMES_DEMO[i%4]} · {key.replace("_"," ")} Test'
            ),
            contact=f'SYN-DEMO-{key.upper().replace("_","-")}-{len(rows(db,Lead,tid)):05}-{i}',
            source="Website",
            city="Islamabad",
            interest=(
                ["Data Science", "IELTS", "Web Development", "Digital Marketing"][i % 4]
                if "Skills" in db.get(Tenant, tid).name
                else [
                    "Bahria Apartment",
                    "DHA Plot",
                    "Commercial Office",
                    "Rental Home",
                ][i % 4]
            ),
            inquiry="Assalam-o-Alaikum, I would like to enroll today. Please share details and the next available consultation.",
            budget=120000 if key == "high_value" else 65000,
            urgency="today" if key in ("high_value", "sla") else "this_week",
            consent=consent,
        )
        r = capture(db, tid, data.model_dump(), user["id"], assign)
        l = db.get(Lead, r["lead"]["id"])
        created.append(l)
        return l

    if key == "burst":
        for i in range(20):
            inject(i, False)
        comparison = allocation_preview(db, tid, created)
        commit_allocation(db, tid, comparison, user["id"])
    else:
        l = inject(consent="opted_out" if key == "opt_out" else "granted")
        if key == "sla":
            tenant = db.get(Tenant, tid)
            tenant.clock = plus(tenant.clock, 240)
            recovery(db, tid)
        if key == "capacity":
            if not l.owner_id:
                raise HTTPException(
                    422, "No initial owner; reset the demo before the capacity scenario"
                )
            reps, loads, _ = load_snapshot(db, tid)
            original = db.get(Rep, l.owner_id)
            previous_capacity = original.capacity
            original.capacity = max(1, loads[original.id])
            audit(
                db,
                tid,
                user["id"],
                "demo_capacity_changed",
                original.id,
                "Simulated capacity constraint",
                {"capacity": previous_capacity},
                {"capacity": original.capacity},
            )
            db.flush()
            plan = allocation_preview(db, tid, [l])
            if not plan["assignments"]:
                raise HTTPException(
                    422, "No alternative capacity; reset the demo before this scenario"
                )
            selected = plan["assignments"][0]
            reassign(
                db,
                user,
                l,
                selected["rep_id"],
                "Demo: manager approves reassignment after adviser capacity constraint",
            )
            trace(
                db,
                l,
                "Allocation",
                "Capacity-driven reassignment",
                {"previous_owner": original.id},
                {
                    "chosen_owner": selected["rep_id"],
                    "utility": selected["utility"],
                    "reason": "Original adviser has no remaining capacity; manager-approved alternate selected.",
                },
                selected["alternatives"],
            )
            for i in range(8):
                inject(i + 1, False)
            comparison = allocation_preview(db, tid, created[1:])
            commit_allocation(db, tid, comparison, user["id"])
        if key in ("appointment", "conversion"):
            if not l.owner_id:
                raise HTTPException(
                    422,
                    "No on-duty capacity. Reset the demo or adjust team availability.",
                )
            task = db.scalar(select(Task).where(Task.lead_id == l.id))
            enqueue(
                db,
                l,
                task,
                "Simulated: Your consultation is available.",
                actor=user["id"],
            )
            process_jobs(db, tid)
            reply(db, l, user["id"])
            transition(db, l, "qualified", user["id"])
            transition(
                db,
                l,
                "appointment",
                user["id"],
                appointment_at=plus(now(db, tid), 1440),
            )
            if key == "conversion":
                transition(db, l, "won", user["id"], verified=True, value=65000)
                analytics_trace(db, l)
        if key == "override":
            reps, loads, clock = load_snapshot(db, tid)
            r = next(
                (
                    r
                    for r in reps
                    if r.id != l.owner_id
                    and r.active
                    and r.shift_start <= clock.hour < r.shift_end
                    and loads[r.id] < r.capacity
                ),
                None,
            )
            if not r:
                raise HTTPException(
                    422, "No alternative available; reset demo or adjust team capacity"
                )
            reassign(
                db,
                user,
                l,
                r.id,
                "Demo: manager chooses an adviser with prior course context",
            )
        if key in ("opt_out", "retry"):
            task = db.scalar(select(Task).where(Task.lead_id == l.id))
            enqueue(
                db,
                l,
                task,
                "Simulated: may we help with your inquiry?",
                key == "retry",
                user["id"],
            )
            process_jobs(db, tid)
    db.flush()
    after = analytics(db, user, 0)
    audit(
        db,
        tid,
        user["id"],
        "scenario_run",
        key,
        "Explicit Demo Lab action",
        {"total": before["total"]},
        {"total": after["total"]},
    )
    return {
        "scenario": key,
        "lead_ids": [l.id for l in created],
        "leads": [serialize(l) for l in created],
        "before": {
            k: before[k] for k in ["total", "overdue", "won", "revenue", "sla_met"]
        },
        "after": {
            k: after[k] for k in ["total", "overdue", "won", "revenue", "sla_met"]
        },
        "comparison": comparison,
        "is_simulated": True,
    }


NAMES_DEMO = ["Fatima", "Hassan", "Noor", "Ahmed"]


class ScheduleIn(BaseModel):
    lead_id: str
    due_at: str
    kind: Literal["follow_up", "consultation", "first_response"] = "follow_up"


@app.post("/api/v1/tasks")
def create_task(data: ScheduleIn, user=Depends(current), db=Depends(db_session)):
    permit(user)
    l = get_lead(db, user, data.lead_id)
    try:
        deadline = dt(data.due_at)
        if deadline.tzinfo is None or deadline <= dt(now(db, l.tenant_id)):
            raise ValueError()
    except ValueError:
        raise HTTPException(
            422, "Due time must be timezone-aware and in the simulated future"
        )
    if l.stage in TERMINAL:
        raise HTTPException(422, "Closed leads cannot receive new follow-ups")
    return serialize(
        schedule(db, l, deadline.astimezone(timezone.utc).isoformat(), data.kind)
    )


# A built frontend can be served from the same origin for cookie-safe offline demos.
from pathlib import Path

web_dist = Path(__file__).resolve().parents[3] / "apps/web/dist"
if web_dist.exists():
    app.mount("/", StaticFiles(directory=str(web_dist), html=True), name="web")
