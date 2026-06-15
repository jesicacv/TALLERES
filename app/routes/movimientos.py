from __future__ import annotations

from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import Select, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.templating import base_context, templates
from app.core.web_auth import require_user
from app.models.cliente import Cliente
from app.models.enums import EstadoOTEnum, TipoItemOTEnum
from app.models.orden_trabajo import OrdenTrabajo
from app.models.ot_checklist import OTChecklist
from app.models.ot_mano_obra import OTManoObra
from app.models.ot_repuestos import OTRepuesto
from app.models.repuesto import Repuesto
from app.models.tecnico import Tecnico
from app.models.usuario import Usuario
from app.models.vehiculo import Vehiculo
from app.services.audit_service import log_audit, model_to_dict
from database.base import get_db

router = APIRouter(prefix="/movimientos", tags=["movimientos"], dependencies=[Depends(require_user)])


def _redirect(url: str) -> RedirectResponse:
    return RedirectResponse(url=url, status_code=303)


def _ot_number(db: Session) -> str:
    max_id = db.scalar(select(func.max(OrdenTrabajo.id))) or 0
    return f"OT-{max_id + 1:06d}"


def _to_optional(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    return value or None


def _ot_or_404(db: Session, ot_id: int) -> OrdenTrabajo:
    ot = db.get(OrdenTrabajo, ot_id)
    if ot is None:
        raise HTTPException(status_code=404, detail="Orden de trabajo no encontrada")
    return ot


@router.get("/ordenes-trabajo", response_class=HTMLResponse)
def ordenes_page(request: Request, db: Session = Depends(get_db), q: str = "") -> HTMLResponse:
    stmt: Select[tuple[OrdenTrabajo]] = select(OrdenTrabajo)
    if q.strip():
        like = f"%{q.strip()}%"
        stmt = stmt.where(
            or_(
                OrdenTrabajo.numero_ot.ilike(like),
                OrdenTrabajo.patente.ilike(like),
                OrdenTrabajo.cliente_rut.ilike(like),
                OrdenTrabajo.glosa_general.ilike(like),
            )
        )
    ordenes = db.scalars(stmt.order_by(OrdenTrabajo.id.desc())).all()
    vehiculos = db.scalars(select(Vehiculo).order_by(Vehiculo.patente)).all()
    usuarios = db.scalars(select(Usuario).where(Usuario.activo.is_(True)).order_by(Usuario.nombre_completo)).all()

    context = {
        "request": request,
        **base_context(),
        "ordenes": ordenes,
        "vehiculos": vehiculos,
        "usuarios": usuarios,
        "estados_ot": [item.value for item in EstadoOTEnum],
        "numero_ot_sugerido": _ot_number(db),
        "q": q,
    }
    return templates.TemplateResponse("pages/movimientos_ordenes.html", context)


@router.post("/ordenes-trabajo/create")
def ordenes_create(
    request: Request,
    numero_ot: str = Form(...),
    patente: str = Form(...),
    recepcionista_id: int | None = Form(default=None),
    fecha_ingreso: date = Form(...),
    fecha_prometida: date | None = Form(default=None),
    fecha_termino: date | None = Form(default=None),
    kms_ingreso: int | None = Form(default=None),
    glosa_general: str | None = Form(default=None),
    forma_pago: str | None = Form(default=None),
    estado: EstadoOTEnum = Form(...),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    vehiculo = db.get(Vehiculo, patente.strip().upper())
    if vehiculo is None:
        raise HTTPException(status_code=400, detail="Vehiculo no existe")

    ot = OrdenTrabajo(
        numero_ot=numero_ot.strip().upper(),
        patente=vehiculo.patente,
        cliente_rut=vehiculo.cliente_rut,
        recepcionista_id=recepcionista_id,
        fecha_ingreso=fecha_ingreso,
        fecha_prometida=fecha_prometida,
        fecha_termino=fecha_termino,
        kms_ingreso=kms_ingreso,
        glosa_general=_to_optional(glosa_general),
        forma_pago=_to_optional(forma_pago),
        estado=estado,
    )
    db.add(ot)
    log_audit(db, request, accion="CREATE", modulo="MOVIMIENTOS_OT", entidad_id=ot.numero_ot, datos_nuevos=model_to_dict(ot))
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="No se pudo crear OT (numero duplicado o datos invalidos)")
    return _redirect("/movimientos/ordenes-trabajo")


@router.get("/ordenes-trabajo/{ot_id}/edit", response_class=HTMLResponse)
def ordenes_edit_page(ot_id: int, request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    ot = _ot_or_404(db, ot_id)
    context = {
        "request": request,
        **base_context(),
        "ot": ot,
        "vehiculos": db.scalars(select(Vehiculo).order_by(Vehiculo.patente)).all(),
        "usuarios": db.scalars(select(Usuario).where(Usuario.activo.is_(True)).order_by(Usuario.nombre_completo)).all(),
        "estados_ot": [item.value for item in EstadoOTEnum],
    }
    return templates.TemplateResponse("pages/movimientos_orden_edit.html", context)


@router.post("/ordenes-trabajo/{ot_id}/edit")
def ordenes_edit(
    request: Request,
    ot_id: int,
    patente: str = Form(...),
    recepcionista_id: int | None = Form(default=None),
    fecha_ingreso: date = Form(...),
    fecha_prometida: date | None = Form(default=None),
    fecha_termino: date | None = Form(default=None),
    kms_ingreso: int | None = Form(default=None),
    glosa_general: str | None = Form(default=None),
    forma_pago: str | None = Form(default=None),
    estado: EstadoOTEnum = Form(...),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    ot = _ot_or_404(db, ot_id)
    vehiculo = db.get(Vehiculo, patente.strip().upper())
    if vehiculo is None:
        raise HTTPException(status_code=400, detail="Vehiculo no existe")

    anterior = model_to_dict(ot)
    ot.patente = vehiculo.patente
    ot.cliente_rut = vehiculo.cliente_rut
    ot.recepcionista_id = recepcionista_id
    ot.fecha_ingreso = fecha_ingreso
    ot.fecha_prometida = fecha_prometida
    ot.fecha_termino = fecha_termino
    ot.kms_ingreso = kms_ingreso
    ot.glosa_general = _to_optional(glosa_general)
    ot.forma_pago = _to_optional(forma_pago)
    ot.estado = estado
    log_audit(db, request, accion="UPDATE", modulo="MOVIMIENTOS_OT", entidad_id=str(ot.id), datos_anteriores=anterior, datos_nuevos=model_to_dict(ot))
    db.commit()
    return _redirect("/movimientos/ordenes-trabajo")


@router.post("/ordenes-trabajo/{ot_id}/delete")
def ordenes_delete(ot_id: int, request: Request, db: Session = Depends(get_db)) -> RedirectResponse:
    ot = db.get(OrdenTrabajo, ot_id)
    if ot is not None:
        anterior = model_to_dict(ot)
        db.delete(ot)
        log_audit(db, request, accion="DELETE", modulo="MOVIMIENTOS_OT", entidad_id=str(ot_id), datos_anteriores=anterior)
        db.commit()
    return _redirect("/movimientos/ordenes-trabajo")


@router.get("/ordenes-trabajo/{ot_id}/mano-obra", response_class=HTMLResponse)
def mano_obra_page(ot_id: int, request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    ot = _ot_or_404(db, ot_id)
    context = {
        "request": request,
        **base_context(),
        "ot": ot,
        "items": db.scalars(select(OTManoObra).where(OTManoObra.ot_id == ot_id).order_by(OTManoObra.id.desc())).all(),
        "tecnicos": db.scalars(select(Tecnico).where(Tecnico.activo.is_(True)).order_by(Tecnico.nombre)).all(),
    }
    return templates.TemplateResponse("pages/movimientos_mano_obra.html", context)


@router.post("/ordenes-trabajo/{ot_id}/mano-obra/create")
def mano_obra_create(
    request: Request,
    ot_id: int,
    tecnico_id: int = Form(...),
    descripcion_trabajo: str = Form(...),
    horas: Decimal = Form(...),
    precio_unitario: Decimal = Form(...),
    descuento_pct: Decimal = Form(default=0),
    bonificacion: Decimal = Form(default=0),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    _ot_or_404(db, ot_id)
    base = horas * precio_unitario
    total_neto = base - (base * descuento_pct / Decimal("100")) - bonificacion
    total_neto = total_neto if total_neto > 0 else Decimal("0")
    total_con_impuesto = total_neto * Decimal("1.19")

    item = OTManoObra(
        ot_id=ot_id,
        tecnico_id=tecnico_id,
        descripcion_trabajo=descripcion_trabajo.strip(),
        horas=horas,
        precio_unitario=precio_unitario,
        descuento_pct=descuento_pct,
        bonificacion=bonificacion,
        total_neto=total_neto,
        total_con_impuesto=total_con_impuesto,
    )
    db.add(item)
    log_audit(db, request, accion="CREATE", modulo="MOVIMIENTOS_MANO_OBRA", entidad_id=str(ot_id), datos_nuevos=model_to_dict(item))
    db.commit()
    return _redirect(f"/movimientos/ordenes-trabajo/{ot_id}/mano-obra")


@router.post("/mano-obra/{item_id}/delete")
def mano_obra_delete(item_id: int, request: Request, db: Session = Depends(get_db)) -> RedirectResponse:
    item = db.get(OTManoObra, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Item de mano de obra no encontrado")
    ot_id = item.ot_id
    anterior = model_to_dict(item)
    db.delete(item)
    log_audit(db, request, accion="DELETE", modulo="MOVIMIENTOS_MANO_OBRA", entidad_id=str(item_id), datos_anteriores=anterior)
    db.commit()
    return _redirect(f"/movimientos/ordenes-trabajo/{ot_id}/mano-obra")


@router.get("/ordenes-trabajo/{ot_id}/repuestos", response_class=HTMLResponse)
def repuestos_page(ot_id: int, request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    ot = _ot_or_404(db, ot_id)
    context = {
        "request": request,
        **base_context(),
        "ot": ot,
        "items": db.scalars(select(OTRepuesto).where(OTRepuesto.ot_id == ot_id).order_by(OTRepuesto.id.desc())).all(),
        "repuestos": db.scalars(select(Repuesto).order_by(Repuesto.nombre)).all(),
        "tipos_item": [item.value for item in TipoItemOTEnum],
    }
    return templates.TemplateResponse("pages/movimientos_repuestos_ot.html", context)


@router.post("/ordenes-trabajo/{ot_id}/repuestos/create")
def repuestos_create(
    request: Request,
    ot_id: int,
    repuesto_codigo: str | None = Form(default=None),
    descripcion: str = Form(...),
    cantidad: Decimal = Form(...),
    precio_costo_unitario: Decimal = Form(default=0),
    precio_venta_unitario: Decimal = Form(default=0),
    descuento_pct: Decimal = Form(default=0),
    es_siniestro: str | None = Form(default=None),
    tipo: TipoItemOTEnum = Form(...),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    _ot_or_404(db, ot_id)
    selected_repuesto = None
    repuesto_key = _to_optional(repuesto_codigo)
    if repuesto_key:
        selected_repuesto = db.get(Repuesto, repuesto_key.upper())

    item = OTRepuesto(
        ot_id=ot_id,
        repuesto_codigo=selected_repuesto.codigo if selected_repuesto else None,
        descripcion=selected_repuesto.nombre if selected_repuesto else descripcion.strip(),
        cantidad=cantidad,
        precio_costo_unitario=selected_repuesto.precio_costo if selected_repuesto else precio_costo_unitario,
        precio_venta_unitario=selected_repuesto.precio_venta if selected_repuesto else precio_venta_unitario,
        descuento_pct=descuento_pct,
        es_siniestro=es_siniestro is not None,
        tipo=tipo,
    )
    db.add(item)
    log_audit(db, request, accion="CREATE", modulo="MOVIMIENTOS_REPUESTOS_OT", entidad_id=str(ot_id), datos_nuevos=model_to_dict(item))
    db.commit()
    return _redirect(f"/movimientos/ordenes-trabajo/{ot_id}/repuestos")


@router.post("/repuestos-ot/{item_id}/delete")
def repuestos_delete(item_id: int, request: Request, db: Session = Depends(get_db)) -> RedirectResponse:
    item = db.get(OTRepuesto, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Item de repuesto no encontrado")
    ot_id = item.ot_id
    anterior = model_to_dict(item)
    db.delete(item)
    log_audit(db, request, accion="DELETE", modulo="MOVIMIENTOS_REPUESTOS_OT", entidad_id=str(item_id), datos_anteriores=anterior)
    db.commit()
    return _redirect(f"/movimientos/ordenes-trabajo/{ot_id}/repuestos")


@router.get("/ordenes-trabajo/{ot_id}/checklist", response_class=HTMLResponse)
def checklist_page(ot_id: int, request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    ot = _ot_or_404(db, ot_id)
    context = {
        "request": request,
        **base_context(),
        "ot": ot,
        "items": db.scalars(select(OTChecklist).where(OTChecklist.ot_id == ot_id).order_by(OTChecklist.id.desc())).all(),
    }
    return templates.TemplateResponse("pages/movimientos_checklist_ot.html", context)


@router.post("/ordenes-trabajo/{ot_id}/checklist/create")
def checklist_create(
    request: Request,
    ot_id: int,
    item: str = Form(...),
    completado: str | None = Form(default=None),
    observacion: str | None = Form(default=None),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    _ot_or_404(db, ot_id)
    check = OTChecklist(
        ot_id=ot_id,
        item=item.strip(),
        completado=completado is not None,
        observacion=_to_optional(observacion),
    )
    db.add(check)
    log_audit(db, request, accion="CREATE", modulo="MOVIMIENTOS_CHECKLIST", entidad_id=str(ot_id), datos_nuevos=model_to_dict(check))
    db.commit()
    return _redirect(f"/movimientos/ordenes-trabajo/{ot_id}/checklist")


@router.post("/checklist/{item_id}/toggle")
def checklist_toggle(item_id: int, request: Request, db: Session = Depends(get_db)) -> RedirectResponse:
    item = db.get(OTChecklist, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Checklist no encontrado")
    anterior = model_to_dict(item)
    item.completado = not item.completado
    ot_id = item.ot_id
    log_audit(db, request, accion="TOGGLE", modulo="MOVIMIENTOS_CHECKLIST", entidad_id=str(item.id), datos_anteriores=anterior, datos_nuevos=model_to_dict(item))
    db.commit()
    return _redirect(f"/movimientos/ordenes-trabajo/{ot_id}/checklist")


@router.post("/checklist/{item_id}/delete")
def checklist_delete(item_id: int, request: Request, db: Session = Depends(get_db)) -> RedirectResponse:
    item = db.get(OTChecklist, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Checklist no encontrado")
    ot_id = item.ot_id
    anterior = model_to_dict(item)
    db.delete(item)
    log_audit(db, request, accion="DELETE", modulo="MOVIMIENTOS_CHECKLIST", entidad_id=str(item_id), datos_anteriores=anterior)
    db.commit()
    return _redirect(f"/movimientos/ordenes-trabajo/{ot_id}/checklist")
