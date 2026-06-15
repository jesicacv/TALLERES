from __future__ import annotations

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.core.templating import base_context, templates
from app.core.web_auth import (
    SESSION_COOKIE,
    clear_session_cookie,
    require_user_pwchange_ok,
    set_session_cookie,
)
from app.models.usuario import Usuario
from app.services.audit_service import log_audit
from app.services.auth_service import authenticate_user, get_user_from_token, logout_session
from database.base import get_db

router = APIRouter(tags=["web-auth"])


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request) -> HTMLResponse:
    context = {"request": request, **base_context(), "error": None}
    return templates.TemplateResponse("pages/login.html", context)


@router.post("/login")
def login_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    ip = request.client.host if request.client else None
    try:
        user, token = authenticate_user(db, username.strip(), password, ip)
    except HTTPException:
        context = {"request": request, **base_context(), "error": "Credenciales invalidas"}
        return templates.TemplateResponse("pages/login.html", context, status_code=401)

    log_audit(
        db,
        request,
        accion="LOGIN",
        modulo="AUTH",
        entidad_id=str(user.id),
        datos_nuevos={"username": user.username, "via": "web"},
        usuario_id=user.id,
    )
    db.commit()

    destino = "/cambiar-password" if user.debe_cambiar_password else "/"
    response = RedirectResponse(destino, status_code=303)
    set_session_cookie(response, token.access_token)
    return response


@router.post("/logout")
def logout_submit(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get(SESSION_COOKIE)
    if token:
        try:
            user = get_user_from_token(db, token)
        except Exception:
            user = None
        try:
            logout_session(db, token)
        except Exception:
            pass
        if user is not None:
            log_audit(
                db,
                request,
                accion="LOGOUT",
                modulo="AUTH",
                entidad_id=str(user.id),
                datos_nuevos={"username": user.username, "via": "web"},
                usuario_id=user.id,
            )
            db.commit()
    response = RedirectResponse("/login", status_code=303)
    clear_session_cookie(response)
    return response


@router.get("/cambiar-password", response_class=HTMLResponse)
def password_change_page(
    request: Request,
    user: Usuario = Depends(require_user_pwchange_ok),
) -> HTMLResponse:
    context = {"request": request, **base_context(), "error": None, "forzado": user.debe_cambiar_password}
    return templates.TemplateResponse("pages/cambiar_password.html", context)


@router.post("/cambiar-password")
def password_change_submit(
    request: Request,
    password_actual: str = Form(...),
    password_nueva: str = Form(...),
    password_confirmacion: str = Form(...),
    user: Usuario = Depends(require_user_pwchange_ok),
    db: Session = Depends(get_db),
):
    def _error(mensaje: str):
        context = {"request": request, **base_context(), "error": mensaje, "forzado": user.debe_cambiar_password}
        return templates.TemplateResponse("pages/cambiar_password.html", context, status_code=400)

    if not verify_password(password_actual, user.password_hash):
        return _error("La contrasena actual es incorrecta")
    if len(password_nueva.strip()) < 8:
        return _error("La nueva contrasena debe tener al menos 8 caracteres")
    if password_nueva != password_confirmacion:
        return _error("La confirmacion no coincide")

    user.password_hash = hash_password(password_nueva.strip())
    user.debe_cambiar_password = False
    log_audit(
        db,
        request,
        accion="PASSWORD_CHANGE",
        modulo="AUTH",
        entidad_id=str(user.id),
        datos_nuevos={"username": user.username},
        usuario_id=user.id,
    )
    db.commit()
    return RedirectResponse("/", status_code=303)
