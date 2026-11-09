import hashlib, secrets
from datetime import datetime, timedelta, timezone
from argon2 import PasswordHasher
from fastapi import Request, HTTPException, Depends
from sqlalchemy import select
from .db import SessionLocal, Session, Membership, User, Rep

ph = PasswordHasher()


def db_session(request: Request):
    # The request middleware owns the transaction, including idempotency results.
    return request.state.db


def current(request: Request, db=Depends(db_session)):
    token = request.cookies.get("lp_session", "")
    session = db.get(Session, hashlib.sha256(token.encode()).hexdigest())
    if not session or session.expires < datetime.now(timezone.utc).isoformat():
        raise HTTPException(401, "Please sign in")
    if request.method not in ("GET", "HEAD", "OPTIONS") and not secrets.compare_digest(
        request.headers.get("X-CSRF-Token", ""), session.csrf
    ):
        raise HTTPException(403, "CSRF token missing or invalid")
    member = db.scalar(select(Membership).where(Membership.user_id == session.user_id))
    if not member:
        raise HTTPException(403, "No active membership")
    user = db.get(User, session.user_id)
    rep = db.scalar(
        select(Rep).where(Rep.tenant_id == member.tenant_id, Rep.user_id == user.id)
    )
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "tenant_id": member.tenant_id,
        "role": member.role,
        "rep_id": rep.id if rep else None,
        "csrf": session.csrf,
    }


def permit(user, roles=("owner", "manager", "operator")):
    if user["role"] not in roles:
        raise HTTPException(403, "Your role cannot perform this action")
