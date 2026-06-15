from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.schemas.auth import AuthUserResponse, LoginRequest, LogoutResponse, TokenResponse
from app.services.audit_service import log_audit
from app.services.auth_service import authenticate_user, get_user_from_token, logout_session, user_to_response
from database.base import get_db

router = APIRouter(prefix="/auth", tags=["auth"])
bearer_scheme = HTTPBearer(auto_error=False)


def _extract_token(credentials: HTTPAuthorizationCredentials | None) -> str:
    if credentials is None or not credentials.credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token requerido")
    return credentials.credentials


def get_current_user(
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> AuthUserResponse:
    token = _extract_token(credentials)
    user = get_user_from_token(db, token)
    return user_to_response(user)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)) -> TokenResponse:
    user, token = authenticate_user(db, payload.username, payload.password, request.client.host if request.client else None)
    log_audit(
        db,
        request,
        accion="LOGIN",
        modulo="AUTH",
        entidad_id=str(user.id),
        datos_nuevos={"username": user.username},
        usuario_id=user.id,
    )
    db.commit()
    return token


@router.post("/logout", response_model=LogoutResponse)
def logout(
    request: Request,
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> LogoutResponse:
    token = _extract_token(credentials)
    user = get_user_from_token(db, token)
    logout_session(db, token)
    log_audit(
        db,
        request,
        accion="LOGOUT",
        modulo="AUTH",
        entidad_id=str(user.id),
        datos_nuevos={"username": user.username},
        usuario_id=user.id,
    )
    db.commit()
    return LogoutResponse(message="Sesion cerrada correctamente")


@router.get("/me", response_model=AuthUserResponse)
def me(user: AuthUserResponse = Depends(get_current_user)) -> AuthUserResponse:
    return user


@router.get("/health")
def auth_health(x_health_check: str | None = Header(default=None)) -> dict[str, str | bool]:
    return {
        "service": "auth",
        "ok": True,
        "header_received": bool(x_health_check),
    }
