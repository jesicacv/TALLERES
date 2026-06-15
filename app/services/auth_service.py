from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy import Select, select
from sqlalchemy.orm import Session, joinedload

from app.core.security import create_access_token, decode_access_token, token_hash, verify_password
from app.models.usuario import IntentoLogin, Sesion, Usuario, UsuarioRol
from app.schemas.auth import AuthUserResponse, TokenResponse, UserInfo
from config.settings import settings


def _active_user_query() -> Select[tuple[Usuario]]:
    return (
        select(Usuario)
        .options(joinedload(Usuario.roles).joinedload(UsuarioRol.rol))
        .where(Usuario.activo.is_(True))
    )


def _register_login_attempt(db: Session, username: str, ip_origen: str | None, success: bool) -> None:
    db.add(IntentoLogin(username_intento=username, ip_origen=ip_origen, exitoso=success))


def authenticate_user(db: Session, username: str, password: str, ip_origen: str | None) -> tuple[Usuario, TokenResponse]:
    user = db.scalar(_active_user_query().where(Usuario.username == username))
    if user is None or not verify_password(password, user.password_hash):
        _register_login_attempt(db, username, ip_origen, False)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales invalidas",
        )

    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=settings.access_token_expire_minutes)

    session_row = Sesion(
        usuario_id=user.id,
        token_hash="pending",
        ip_origen=ip_origen,
        expira_en=expires_at,
        activa=True,
    )
    db.add(session_row)
    db.flush()

    jwt_token = create_access_token(subject=user.username, session_id=session_row.id)
    session_row.token_hash = token_hash(jwt_token)

    user.ultimo_acceso = now
    _register_login_attempt(db, username, ip_origen, True)
    db.commit()

    return user, TokenResponse(access_token=jwt_token, expires_at=expires_at)


def get_user_from_token(db: Session, raw_token: str) -> Usuario:
    payload = decode_access_token(raw_token)
    username = payload.get("sub")
    session_id = payload.get("sid")

    if not username or not session_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token invalido")

    try:
        session_uuid = uuid.UUID(session_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token invalido") from exc

    session_row = db.scalar(select(Sesion).where(Sesion.id == session_uuid))
    if session_row is None or not session_row.activa:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Sesion invalida")

    if session_row.token_hash != token_hash(raw_token):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Sesion invalida")

    now = datetime.now(timezone.utc)
    if session_row.expira_en <= now:
        session_row.activa = False
        db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Sesion expirada")

    user = db.scalar(
        _active_user_query().where(
            Usuario.id == session_row.usuario_id,
            Usuario.username == username,
        )
    )
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario no autorizado")

    return user


def logout_session(db: Session, raw_token: str) -> None:
    payload = decode_access_token(raw_token)
    session_id = payload.get("sid")
    if not session_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token invalido")

    try:
        session_uuid = uuid.UUID(session_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token invalido") from exc

    session_row = db.scalar(select(Sesion).where(Sesion.id == session_uuid))
    if session_row is None:
        return

    session_row.activa = False
    db.commit()


def user_to_response(user: Usuario) -> AuthUserResponse:
    role_names = [rel.rol.nombre for rel in user.roles if rel.rol is not None]
    return AuthUserResponse(usuario=UserInfo.model_validate(user), roles=sorted(set(role_names)))
