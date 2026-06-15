from __future__ import annotations

from fastapi import Depends, Request, Response
from sqlalchemy.orm import Session

from app.models.usuario import Usuario
from app.services.auth_service import get_user_from_token
from config.settings import settings
from database.base import get_db

SESSION_COOKIE = "session_token"
LOGIN_PATH = "/login"
PASSWORD_CHANGE_PATH = "/cambiar-password"


class NotAuthenticatedError(Exception):
    """No hay sesion web valida; el handler redirige a /login."""


class PasswordChangeRequiredError(Exception):
    """Sesion valida pero el usuario debe cambiar su password antes de continuar."""


def set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=SESSION_COOKIE,
        value=token,
        max_age=settings.access_token_expire_minutes * 60,
        httponly=True,
        samesite="lax",
        secure=settings.cookie_secure,
        path="/",
    )


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(key=SESSION_COOKIE, path="/")


def _user_from_cookie(request: Request, db: Session) -> Usuario:
    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        raise NotAuthenticatedError
    try:
        user = get_user_from_token(db, token)
    except Exception as exc:  # token/sesion invalida, inactiva o expirada
        raise NotAuthenticatedError from exc
    request.state.user = user  # disponible para los templates (navbar)
    return user


def require_user(request: Request, db: Session = Depends(get_db)) -> Usuario:
    """Guard de paginas protegidas: exige sesion y password al dia."""
    user = _user_from_cookie(request, db)
    if user.debe_cambiar_password:
        raise PasswordChangeRequiredError
    return user


def require_user_pwchange_ok(request: Request, db: Session = Depends(get_db)) -> Usuario:
    """Guard relajado: exige sesion pero NO fuerza el cambio (para la propia pantalla de cambio)."""
    return _user_from_cookie(request, db)
