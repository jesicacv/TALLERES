from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from config.settings import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, password_hash: str) -> bool:
    return pwd_context.verify(plain_password, password_hash)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(subject: str, session_id: uuid.UUID, expires_minutes: int | None = None) -> str:
    expire_delta = timedelta(minutes=expires_minutes or settings.access_token_expire_minutes)
    expire_at = datetime.now(timezone.utc) + expire_delta
    payload = {
        "sub": subject,
        "sid": str(session_id),
        "exp": expire_at,
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    except JWTError as exc:
        raise ValueError("Token JWT invalido o expirado") from exc
    return payload


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
