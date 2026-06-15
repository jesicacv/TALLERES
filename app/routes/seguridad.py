from __future__ import annotations

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import Select, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.core.templating import base_context, templates
from app.core.web_auth import require_user
from app.models.usuario import Permiso, Rol, RolPermiso, Usuario, UsuarioRol
from app.models.auditoria import Auditoria
from app.services.audit_service import log_audit, model_to_dict
from database.base import get_db

router = APIRouter(prefix="/seguridad", tags=["seguridad"], dependencies=[Depends(require_user)])


def _redirect(url: str) -> RedirectResponse:
    return RedirectResponse(url=url, status_code=303)


def _sync_user_roles(db: Session, usuario: Usuario, role_ids: list[int]) -> None:
    valid_ids = {rol.id for rol in db.scalars(select(Rol).where(Rol.id.in_(role_ids))).all()} if role_ids else set()
    current_ids = {rel.rol_id for rel in usuario.roles}

    for rel in list(usuario.roles):
        if rel.rol_id not in valid_ids:
            db.delete(rel)

    for rid in valid_ids - current_ids:
        db.add(UsuarioRol(usuario_id=usuario.id, rol_id=rid))


def _sync_role_permisos(db: Session, rol: Rol, permiso_ids: list[int]) -> None:
    valid_ids = {perm.id for perm in db.scalars(select(Permiso).where(Permiso.id.in_(permiso_ids))).all()} if permiso_ids else set()
    current_ids = {rel.permiso_id for rel in rol.permisos}

    for rel in list(rol.permisos):
        if rel.permiso_id not in valid_ids:
            db.delete(rel)

    for pid in valid_ids - current_ids:
        db.add(RolPermiso(rol_id=rol.id, permiso_id=pid))


@router.get("/usuarios", response_class=HTMLResponse)
def usuarios_page(request: Request, db: Session = Depends(get_db), q: str = "") -> HTMLResponse:
    stmt: Select[tuple[Usuario]] = select(Usuario)
    if q.strip():
        like = f"%{q.strip()}%"
        stmt = stmt.where(
            or_(
                Usuario.username.ilike(like),
                Usuario.email.ilike(like),
                Usuario.nombre_completo.ilike(like),
            )
        )
    usuarios = db.scalars(stmt.order_by(Usuario.username)).all()
    roles = db.scalars(select(Rol).order_by(Rol.nombre)).all()

    context = {
        "request": request,
        **base_context(),
        "usuarios": usuarios,
        "roles": roles,
        "q": q,
    }
    return templates.TemplateResponse("pages/seguridad_usuarios.html", context)


@router.post("/usuarios/create")
def usuarios_create(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    nombre_completo: str = Form(...),
    password: str = Form(...),
    role_ids: list[int] = Form(default=[]),
    activo: str | None = Form(default=None),
    debe_cambiar_password: str | None = Form(default=None),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    usuario = Usuario(
        username=username.strip(),
        email=email.strip(),
        nombre_completo=nombre_completo.strip(),
        password_hash=hash_password(password),
        activo=activo is not None,
        debe_cambiar_password=debe_cambiar_password is not None,
    )
    db.add(usuario)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="No se pudo crear usuario (username/email duplicado)")

    _sync_user_roles(db, usuario, role_ids)
    log_audit(db, request, accion="CREATE", modulo="SEGURIDAD_USUARIOS", entidad_id=str(usuario.id), datos_nuevos=model_to_dict(usuario))
    db.commit()
    return _redirect("/seguridad/usuarios")


@router.get("/usuarios/{usuario_id}/edit", response_class=HTMLResponse)
def usuarios_edit_page(usuario_id: int, request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    usuario = db.get(Usuario, usuario_id)
    if usuario is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    roles = db.scalars(select(Rol).order_by(Rol.nombre)).all()
    current_roles = {rel.rol_id for rel in usuario.roles}

    context = {
        "request": request,
        **base_context(),
        "usuario": usuario,
        "roles": roles,
        "current_roles": current_roles,
    }
    return templates.TemplateResponse("pages/seguridad_usuario_edit.html", context)


@router.post("/usuarios/{usuario_id}/edit")
def usuarios_edit(
    request: Request,
    usuario_id: int,
    email: str = Form(...),
    nombre_completo: str = Form(...),
    new_password: str | None = Form(default=None),
    role_ids: list[int] = Form(default=[]),
    activo: str | None = Form(default=None),
    debe_cambiar_password: str | None = Form(default=None),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    usuario = db.get(Usuario, usuario_id)
    if usuario is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    anterior = model_to_dict(usuario)
    usuario.email = email.strip()
    usuario.nombre_completo = nombre_completo.strip()
    usuario.activo = activo is not None
    usuario.debe_cambiar_password = debe_cambiar_password is not None
    if new_password and new_password.strip():
        usuario.password_hash = hash_password(new_password.strip())

    _sync_user_roles(db, usuario, role_ids)
    log_audit(
        db,
        request,
        accion="UPDATE",
        modulo="SEGURIDAD_USUARIOS",
        entidad_id=str(usuario.id),
        datos_anteriores=anterior,
        datos_nuevos=model_to_dict(usuario),
    )
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="No se pudo editar usuario (email duplicado)")
    return _redirect("/seguridad/usuarios")


@router.post("/usuarios/{usuario_id}/delete")
def usuarios_delete(usuario_id: int, request: Request, db: Session = Depends(get_db)) -> RedirectResponse:
    usuario = db.get(Usuario, usuario_id)
    if usuario is not None:
        anterior = model_to_dict(usuario)
        db.delete(usuario)
        log_audit(db, request, accion="DELETE", modulo="SEGURIDAD_USUARIOS", entidad_id=str(usuario_id), datos_anteriores=anterior)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise HTTPException(status_code=400, detail="No se puede eliminar usuario con referencias activas")
    return _redirect("/seguridad/usuarios")


@router.get("/roles", response_class=HTMLResponse)
def roles_page(request: Request, db: Session = Depends(get_db), q: str = "") -> HTMLResponse:
    stmt: Select[tuple[Rol]] = select(Rol)
    if q.strip():
        like = f"%{q.strip()}%"
        stmt = stmt.where(Rol.nombre.ilike(like))
    roles = db.scalars(stmt.order_by(Rol.nombre)).all()
    permisos = db.scalars(select(Permiso).order_by(Permiso.modulo, Permiso.codigo)).all()

    context = {
        "request": request,
        **base_context(),
        "roles": roles,
        "permisos": permisos,
        "q": q,
    }
    return templates.TemplateResponse("pages/seguridad_roles.html", context)


@router.post("/roles/create")
def roles_create(
    request: Request,
    nombre: str = Form(...),
    descripcion: str | None = Form(default=None),
    permiso_ids: list[int] = Form(default=[]),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    rol = Rol(nombre=nombre.strip().upper(), descripcion=descripcion.strip() if descripcion else None)
    db.add(rol)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="No se pudo crear rol (nombre duplicado)")

    _sync_role_permisos(db, rol, permiso_ids)
    log_audit(db, request, accion="CREATE", modulo="SEGURIDAD_ROLES", entidad_id=str(rol.id), datos_nuevos=model_to_dict(rol))
    db.commit()
    return _redirect("/seguridad/roles")


@router.get("/roles/{rol_id}/edit", response_class=HTMLResponse)
def roles_edit_page(rol_id: int, request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    rol = db.get(Rol, rol_id)
    if rol is None:
        raise HTTPException(status_code=404, detail="Rol no encontrado")
    permisos = db.scalars(select(Permiso).order_by(Permiso.modulo, Permiso.codigo)).all()
    current_permisos = {rel.permiso_id for rel in rol.permisos}
    context = {
        "request": request,
        **base_context(),
        "rol": rol,
        "permisos": permisos,
        "current_permisos": current_permisos,
    }
    return templates.TemplateResponse("pages/seguridad_rol_edit.html", context)


@router.post("/roles/{rol_id}/edit")
def roles_edit(
    request: Request,
    rol_id: int,
    nombre: str = Form(...),
    descripcion: str | None = Form(default=None),
    permiso_ids: list[int] = Form(default=[]),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    rol = db.get(Rol, rol_id)
    if rol is None:
        raise HTTPException(status_code=404, detail="Rol no encontrado")

    anterior = model_to_dict(rol)
    rol.nombre = nombre.strip().upper()
    rol.descripcion = descripcion.strip() if descripcion else None
    _sync_role_permisos(db, rol, permiso_ids)
    log_audit(
        db,
        request,
        accion="UPDATE",
        modulo="SEGURIDAD_ROLES",
        entidad_id=str(rol.id),
        datos_anteriores=anterior,
        datos_nuevos=model_to_dict(rol),
    )
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="No se pudo editar rol (nombre duplicado)")
    return _redirect("/seguridad/roles")


@router.post("/roles/{rol_id}/delete")
def roles_delete(rol_id: int, request: Request, db: Session = Depends(get_db)) -> RedirectResponse:
    rol = db.get(Rol, rol_id)
    if rol is not None:
        anterior = model_to_dict(rol)
        db.delete(rol)
        log_audit(db, request, accion="DELETE", modulo="SEGURIDAD_ROLES", entidad_id=str(rol_id), datos_anteriores=anterior)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise HTTPException(status_code=400, detail="No se puede eliminar rol asignado a usuarios")
    return _redirect("/seguridad/roles")


@router.get("/permisos", response_class=HTMLResponse)
def permisos_page(request: Request, db: Session = Depends(get_db), q: str = "") -> HTMLResponse:
    stmt: Select[tuple[Permiso]] = select(Permiso)
    if q.strip():
        like = f"%{q.strip()}%"
        stmt = stmt.where(or_(Permiso.codigo.ilike(like), Permiso.modulo.ilike(like), Permiso.descripcion.ilike(like)))
    permisos = db.scalars(stmt.order_by(Permiso.modulo, Permiso.codigo)).all()

    context = {
        "request": request,
        **base_context(),
        "permisos": permisos,
        "q": q,
    }
    return templates.TemplateResponse("pages/seguridad_permisos.html", context)


@router.post("/permisos/create")
def permisos_create(
    request: Request,
    codigo: str = Form(...),
    modulo: str = Form(...),
    descripcion: str | None = Form(default=None),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    permiso = Permiso(codigo=codigo.strip(), modulo=modulo.strip(), descripcion=descripcion.strip() if descripcion else None)
    db.add(permiso)
    log_audit(
        db,
        request,
        accion="CREATE",
        modulo="SEGURIDAD_PERMISOS",
        entidad_id=permiso.codigo,
        datos_nuevos={"codigo": permiso.codigo, "modulo": permiso.modulo, "descripcion": permiso.descripcion},
    )
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="No se pudo crear permiso (codigo duplicado)")
    return _redirect("/seguridad/permisos")


@router.get("/permisos/{permiso_id}/edit", response_class=HTMLResponse)
def permisos_edit_page(permiso_id: int, request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    permiso = db.get(Permiso, permiso_id)
    if permiso is None:
        raise HTTPException(status_code=404, detail="Permiso no encontrado")
    context = {"request": request, **base_context(), "permiso": permiso}
    return templates.TemplateResponse("pages/seguridad_permiso_edit.html", context)


@router.post("/permisos/{permiso_id}/edit")
def permisos_edit(
    request: Request,
    permiso_id: int,
    codigo: str = Form(...),
    modulo: str = Form(...),
    descripcion: str | None = Form(default=None),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    permiso = db.get(Permiso, permiso_id)
    if permiso is None:
        raise HTTPException(status_code=404, detail="Permiso no encontrado")

    anterior = model_to_dict(permiso)
    permiso.codigo = codigo.strip()
    permiso.modulo = modulo.strip()
    permiso.descripcion = descripcion.strip() if descripcion else None
    log_audit(
        db,
        request,
        accion="UPDATE",
        modulo="SEGURIDAD_PERMISOS",
        entidad_id=str(permiso.id),
        datos_anteriores=anterior,
        datos_nuevos=model_to_dict(permiso),
    )
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="No se pudo editar permiso (codigo duplicado)")
    return _redirect("/seguridad/permisos")


@router.post("/permisos/{permiso_id}/delete")
def permisos_delete(permiso_id: int, request: Request, db: Session = Depends(get_db)) -> RedirectResponse:
    permiso = db.get(Permiso, permiso_id)
    if permiso is not None:
        anterior = model_to_dict(permiso)
        db.delete(permiso)
        log_audit(db, request, accion="DELETE", modulo="SEGURIDAD_PERMISOS", entidad_id=str(permiso_id), datos_anteriores=anterior)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise HTTPException(status_code=400, detail="No se puede eliminar permiso asignado a roles")
    return _redirect("/seguridad/permisos")

@router.get("/auditoria", response_class=HTMLResponse)
def auditoria_page(request: Request, db: Session = Depends(get_db), q: str = "", modulo: str = "") -> HTMLResponse:
    stmt: Select[tuple[Auditoria]] = select(Auditoria)
    if q.strip():
        like = f"%{q.strip()}%"
        stmt = stmt.where(or_(Auditoria.accion.ilike(like), Auditoria.entidad_id.ilike(like)))
    if modulo.strip():
        stmt = stmt.where(Auditoria.modulo == modulo.strip())

    auditorias = db.scalars(stmt.order_by(Auditoria.fecha.desc()).limit(200)).all()
    modulos = db.scalars(select(Auditoria.modulo).distinct().order_by(Auditoria.modulo)).all()
    context = {
        "request": request,
        **base_context(),
        "auditorias": auditorias,
        "modulos": modulos,
        "q": q,
        "modulo": modulo,
    }
    return templates.TemplateResponse("pages/seguridad_auditoria.html", context)
