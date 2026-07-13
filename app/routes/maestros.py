from __future__ import annotations

from decimal import Decimal

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import Select, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.templating import base_context, templates
from app.core.web_auth import require_user
from app.models.cliente import Cliente
from app.models.enums import TipoVehiculoEnum
from app.models.repuesto import Repuesto
from app.models.tecnico import Tecnico
from app.models.vehiculo import Vehiculo
from app.services.audit_service import log_audit, model_to_dict
from database.base import get_db

router = APIRouter(prefix="/maestros", tags=["maestros"], dependencies=[Depends(require_user)])


def _to_optional(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned if cleaned else None


def _redirect(url: str) -> RedirectResponse:
    return RedirectResponse(url=url, status_code=303)


@router.get("/clientes", response_class=HTMLResponse)
def clientes_page(request: Request, db: Session = Depends(get_db), q: str = "") -> HTMLResponse:
    stmt: Select[tuple[Cliente]] = select(Cliente)
    if q.strip():
        like = f"%{q.strip()}%"
        stmt = stmt.where(or_(Cliente.rut.ilike(like), Cliente.nombre.ilike(like)))
    clientes = db.scalars(stmt.order_by(Cliente.nombre)).all()

    context = {
        "request": request,
        **base_context(),
        "clientes": clientes,
        "q": q,
    }
    return templates.TemplateResponse("pages/maestros_clientes.html", context)


@router.post("/clientes/create")
def clientes_create(
    request: Request,
    rut: str = Form(...),
    nombre: str = Form(...),
    direccion: str | None = Form(default=None),
    ciudad: str | None = Form(default=None),
    comuna: str | None = Form(default=None),
    fono_particular: str | None = Form(default=None),
    fono_oficina: str | None = Form(default=None),
    celular: str | None = Form(default=None),
    email: str | None = Form(default=None),
    forma_pago_default: str | None = Form(default=None),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    cliente = Cliente(
        rut=rut.strip().upper(),
        nombre=nombre.strip(),
        direccion=_to_optional(direccion),
        ciudad=_to_optional(ciudad),
        comuna=_to_optional(comuna),
        fono_particular=_to_optional(fono_particular),
        fono_oficina=_to_optional(fono_oficina),
        celular=_to_optional(celular),
        email=_to_optional(email),
        forma_pago_default=_to_optional(forma_pago_default),
    )
    db.add(cliente)
    log_audit(db, request, accion="CREATE", modulo="MAESTROS_CLIENTES", entidad_id=cliente.rut, datos_nuevos=model_to_dict(cliente))
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="No se pudo crear cliente (RUT duplicado o datos invalidos)")
    return _redirect("/maestros/clientes")


@router.get("/clientes/{rut}/edit", response_class=HTMLResponse)
def clientes_edit_page(rut: str, request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    cliente = db.get(Cliente, rut.upper())
    if cliente is None:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    context = {"request": request, **base_context(), "cliente": cliente}
    return templates.TemplateResponse("pages/maestros_cliente_edit.html", context)


@router.post("/clientes/{rut}/edit")
def clientes_edit(
    request: Request,
    rut: str,
    nombre: str = Form(...),
    direccion: str | None = Form(default=None),
    ciudad: str | None = Form(default=None),
    comuna: str | None = Form(default=None),
    fono_particular: str | None = Form(default=None),
    fono_oficina: str | None = Form(default=None),
    celular: str | None = Form(default=None),
    email: str | None = Form(default=None),
    forma_pago_default: str | None = Form(default=None),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    cliente = db.get(Cliente, rut.upper())
    if cliente is None:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    anterior = model_to_dict(cliente)
    cliente.nombre = nombre.strip()
    cliente.direccion = _to_optional(direccion)
    cliente.ciudad = _to_optional(ciudad)
    cliente.comuna = _to_optional(comuna)
    cliente.fono_particular = _to_optional(fono_particular)
    cliente.fono_oficina = _to_optional(fono_oficina)
    cliente.celular = _to_optional(celular)
    cliente.email = _to_optional(email)
    cliente.forma_pago_default = _to_optional(forma_pago_default)

    log_audit(db, request, accion="UPDATE", modulo="MAESTROS_CLIENTES", entidad_id=cliente.rut, datos_anteriores=anterior, datos_nuevos=model_to_dict(cliente))
    db.commit()
    return _redirect("/maestros/clientes")


@router.post("/clientes/{rut}/delete")
def clientes_delete(rut: str, request: Request, db: Session = Depends(get_db)) -> RedirectResponse:
    cliente = db.get(Cliente, rut.upper())
    if cliente is not None:
        anterior = model_to_dict(cliente)
        db.delete(cliente)
        log_audit(db, request, accion="DELETE", modulo="MAESTROS_CLIENTES", entidad_id=rut.upper(), datos_anteriores=anterior)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise HTTPException(status_code=400, detail="No se puede eliminar cliente con vehiculos asociados")
    return _redirect("/maestros/clientes")


@router.get("/vehiculos", response_class=HTMLResponse)
def vehiculos_page(request: Request, db: Session = Depends(get_db), q: str = "") -> HTMLResponse:
    stmt: Select[tuple[Vehiculo]] = select(Vehiculo)
    if q.strip():
        like = f"%{q.strip()}%"
        stmt = stmt.where(
            or_(
                Vehiculo.patente.ilike(like),
                Vehiculo.marca.ilike(like),
                Vehiculo.modelo.ilike(like),
                Vehiculo.cliente_rut.ilike(like),
            )
        )
    vehiculos = db.scalars(stmt.order_by(Vehiculo.patente)).all()
    clientes = db.scalars(select(Cliente).order_by(Cliente.nombre)).all()

    context = {
        "request": request,
        **base_context(),
        "vehiculos": vehiculos,
        "clientes": clientes,
        "tipos_vehiculo": [item.value for item in TipoVehiculoEnum],
        "q": q,
    }
    return templates.TemplateResponse("pages/maestros_vehiculos.html", context)


@router.post("/vehiculos/create")
def vehiculos_create(
    request: Request,
    patente: str = Form(...),
    cliente_rut: str = Form(...),
    marca: str = Form(...),
    modelo: str = Form(...),
    sub_modelo: str | None = Form(default=None),
    tipo: TipoVehiculoEnum = Form(...),
    anio: int | None = Form(default=None),
    color: str | None = Form(default=None),
    chasis_vin: str | None = Form(default=None),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    if db.get(Cliente, cliente_rut.upper()) is None:
        raise HTTPException(status_code=400, detail="Cliente no existe para el vehiculo")

    vehiculo = Vehiculo(
        patente=patente.strip().upper(),
        cliente_rut=cliente_rut.strip().upper(),
        marca=marca.strip(),
        modelo=modelo.strip(),
        sub_modelo=_to_optional(sub_modelo),
        tipo=tipo,
        anio=anio,
        color=_to_optional(color),
        chasis_vin=_to_optional(chasis_vin),
    )
    db.add(vehiculo)
    log_audit(db, request, accion="CREATE", modulo="MAESTROS_VEHICULOS", entidad_id=vehiculo.patente, datos_nuevos=model_to_dict(vehiculo))
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="No se pudo crear vehiculo (patente/chasis duplicado o FK invalida)")
    return _redirect("/maestros/vehiculos")


@router.get("/vehiculos/{patente}/edit", response_class=HTMLResponse)
def vehiculos_edit_page(patente: str, request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    vehiculo = db.get(Vehiculo, patente.upper())
    if vehiculo is None:
        raise HTTPException(status_code=404, detail="Vehiculo no encontrado")

    context = {
        "request": request,
        **base_context(),
        "vehiculo": vehiculo,
        "clientes": db.scalars(select(Cliente).order_by(Cliente.nombre)).all(),
        "tipos_vehiculo": [item.value for item in TipoVehiculoEnum],
    }
    return templates.TemplateResponse("pages/maestros_vehiculo_edit.html", context)


@router.post("/vehiculos/{patente}/edit")
def vehiculos_edit(
    request: Request,
    patente: str,
    cliente_rut: str = Form(...),
    marca: str = Form(...),
    modelo: str = Form(...),
    sub_modelo: str | None = Form(default=None),
    tipo: TipoVehiculoEnum = Form(...),
    anio: int | None = Form(default=None),
    color: str | None = Form(default=None),
    chasis_vin: str | None = Form(default=None),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    vehiculo = db.get(Vehiculo, patente.upper())
    if vehiculo is None:
        raise HTTPException(status_code=404, detail="Vehiculo no encontrado")

    if db.get(Cliente, cliente_rut.upper()) is None:
        raise HTTPException(status_code=400, detail="Cliente no existe para el vehiculo")

    anterior = model_to_dict(vehiculo)
    vehiculo.cliente_rut = cliente_rut.strip().upper()
    vehiculo.marca = marca.strip()
    vehiculo.modelo = modelo.strip()
    vehiculo.sub_modelo = _to_optional(sub_modelo)
    vehiculo.tipo = tipo
    vehiculo.anio = anio
    vehiculo.color = _to_optional(color)
    vehiculo.chasis_vin = _to_optional(chasis_vin)

    log_audit(db, request, accion="UPDATE", modulo="MAESTROS_VEHICULOS", entidad_id=vehiculo.patente, datos_anteriores=anterior, datos_nuevos=model_to_dict(vehiculo))
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="No se pudo editar vehiculo (chasis duplicado o datos invalidos)")
    return _redirect("/maestros/vehiculos")


@router.post("/vehiculos/{patente}/delete")
def vehiculos_delete(patente: str, request: Request, db: Session = Depends(get_db)) -> RedirectResponse:
    vehiculo = db.get(Vehiculo, patente.upper())
    if vehiculo is not None:
        anterior = model_to_dict(vehiculo)
        db.delete(vehiculo)
        log_audit(db, request, accion="DELETE", modulo="MAESTROS_VEHICULOS", entidad_id=patente.upper(), datos_anteriores=anterior)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise HTTPException(status_code=400, detail="No se puede eliminar vehiculo con ordenes de trabajo asociadas")
    return _redirect("/maestros/vehiculos")


@router.get("/tecnicos", response_class=HTMLResponse)
def tecnicos_page(request: Request, db: Session = Depends(get_db), q: str = "") -> HTMLResponse:
    stmt: Select[tuple[Tecnico]] = select(Tecnico)
    if q.strip():
        like = f"%{q.strip()}%"
        stmt = stmt.where(or_(Tecnico.codigo.ilike(like), Tecnico.nombre.ilike(like)))
    tecnicos = db.scalars(stmt.order_by(Tecnico.nombre)).all()

    context = {
        "request": request,
        **base_context(),
        "tecnicos": tecnicos,
        "q": q,
    }
    return templates.TemplateResponse("pages/maestros_tecnicos.html", context)


@router.post("/tecnicos/create")
def tecnicos_create(
    request: Request,
    codigo: str = Form(...),
    nombre: str = Form(...),
    activo: str | None = Form(default=None),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    tecnico = Tecnico(
        codigo=codigo.strip().upper(),
        nombre=nombre.strip(),
        activo=activo is not None,
    )
    db.add(tecnico)
    log_audit(db, request, accion="CREATE", modulo="MAESTROS_TECNICOS", entidad_id=tecnico.codigo, datos_nuevos=model_to_dict(tecnico))
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="No se pudo crear tecnico (codigo duplicado)")
    return _redirect("/maestros/tecnicos")


@router.get("/tecnicos/{tecnico_id}/edit", response_class=HTMLResponse)
def tecnicos_edit_page(tecnico_id: int, request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    tecnico = db.get(Tecnico, tecnico_id)
    if tecnico is None:
        raise HTTPException(status_code=404, detail="Tecnico no encontrado")
    context = {"request": request, **base_context(), "tecnico": tecnico}
    return templates.TemplateResponse("pages/maestros_tecnico_edit.html", context)


@router.post("/tecnicos/{tecnico_id}/edit")
def tecnicos_edit(
    request: Request,
    tecnico_id: int,
    codigo: str = Form(...),
    nombre: str = Form(...),
    activo: str | None = Form(default=None),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    tecnico = db.get(Tecnico, tecnico_id)
    if tecnico is None:
        raise HTTPException(status_code=404, detail="Tecnico no encontrado")

    anterior = model_to_dict(tecnico)
    tecnico.codigo = codigo.strip().upper()
    tecnico.nombre = nombre.strip()
    tecnico.activo = activo is not None
    log_audit(db, request, accion="UPDATE", modulo="MAESTROS_TECNICOS", entidad_id=str(tecnico.id), datos_anteriores=anterior, datos_nuevos=model_to_dict(tecnico))
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="No se pudo editar tecnico (codigo duplicado)")
    return _redirect("/maestros/tecnicos")


@router.post("/tecnicos/{tecnico_id}/delete")
def tecnicos_delete(tecnico_id: int, request: Request, db: Session = Depends(get_db)) -> RedirectResponse:
    tecnico = db.get(Tecnico, tecnico_id)
    if tecnico is not None:
        anterior = model_to_dict(tecnico)
        db.delete(tecnico)
        log_audit(db, request, accion="DELETE", modulo="MAESTROS_TECNICOS", entidad_id=str(tecnico_id), datos_anteriores=anterior)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise HTTPException(status_code=400, detail="No se puede eliminar tecnico con mano de obra asociada")
    return _redirect("/maestros/tecnicos")


@router.get("/repuestos", response_class=HTMLResponse)
def repuestos_page(request: Request, db: Session = Depends(get_db), q: str = "") -> HTMLResponse:
    stmt: Select[tuple[Repuesto]] = select(Repuesto)
    if q.strip():
        like = f"%{q.strip()}%"
        stmt = stmt.where(or_(Repuesto.codigo.ilike(like), Repuesto.nombre.ilike(like)))
    repuestos = db.scalars(stmt.order_by(Repuesto.nombre)).all()

    context = {
        "request": request,
        **base_context(),
        "repuestos": repuestos,
        "q": q,
    }
    return templates.TemplateResponse("pages/maestros_repuestos.html", context)


@router.post("/repuestos/create")
def repuestos_create(
    request: Request,
    codigo: str = Form(...),
    nombre: str = Form(...),
    precio_costo: Decimal = Form(...),
    precio_venta: Decimal = Form(...),
    stock_actual: int = Form(...),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    repuesto = Repuesto(
        codigo=codigo.strip().upper(),
        nombre=nombre.strip(),
        precio_costo=precio_costo,
        precio_venta=precio_venta,
        stock_actual=stock_actual,
    )
    db.add(repuesto)
    log_audit(db, request, accion="CREATE", modulo="MAESTROS_REPUESTOS", entidad_id=repuesto.codigo, datos_nuevos=model_to_dict(repuesto))
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="No se pudo crear repuesto (codigo duplicado)")
    return _redirect("/maestros/repuestos")


@router.get("/repuestos/{codigo}/edit", response_class=HTMLResponse)
def repuestos_edit_page(codigo: str, request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    repuesto = db.get(Repuesto, codigo.upper())
    if repuesto is None:
        raise HTTPException(status_code=404, detail="Repuesto no encontrado")
    context = {"request": request, **base_context(), "repuesto": repuesto}
    return templates.TemplateResponse("pages/maestros_repuesto_edit.html", context)


@router.post("/repuestos/{codigo}/edit")
def repuestos_edit(
    request: Request,
    codigo: str,
    nombre: str = Form(...),
    precio_costo: Decimal = Form(...),
    precio_venta: Decimal = Form(...),
    stock_actual: int = Form(...),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    repuesto = db.get(Repuesto, codigo.upper())
    if repuesto is None:
        raise HTTPException(status_code=404, detail="Repuesto no encontrado")

    anterior = model_to_dict(repuesto)
    repuesto.nombre = nombre.strip()
    repuesto.precio_costo = precio_costo
    repuesto.precio_venta = precio_venta
    repuesto.stock_actual = stock_actual
    log_audit(db, request, accion="UPDATE", modulo="MAESTROS_REPUESTOS", entidad_id=repuesto.codigo, datos_anteriores=anterior, datos_nuevos=model_to_dict(repuesto))
    db.commit()
    return _redirect("/maestros/repuestos")


@router.post("/repuestos/{codigo}/delete")
def repuestos_delete(codigo: str, request: Request, db: Session = Depends(get_db)) -> RedirectResponse:
    repuesto = db.get(Repuesto, codigo.upper())
    if repuesto is not None:
        anterior = model_to_dict(repuesto)
        db.delete(repuesto)
        log_audit(db, request, accion="DELETE", modulo="MAESTROS_REPUESTOS", entidad_id=codigo.upper(), datos_anteriores=anterior)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise HTTPException(status_code=400, detail="No se puede eliminar repuesto con items OT asociados")
    return _redirect("/maestros/repuestos")
