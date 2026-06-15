from datetime import date

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.templating import base_context, templates
from app.core.web_auth import require_user
from app.models.cliente import Cliente
from app.models.enums import EstadoOTEnum
from app.models.orden_trabajo import OrdenTrabajo
from app.models.repuesto import Repuesto
from app.models.tecnico import Tecnico
from app.models.vehiculo import Vehiculo
from database.base import get_db

router = APIRouter(tags=["web"], dependencies=[Depends(require_user)])


def dashboard_kpis(db: Session) -> dict[str, int]:
    today = date.today()
    abiertas = db.scalar(select(func.count()).select_from(OrdenTrabajo).where(OrdenTrabajo.estado == EstadoOTEnum.ABIERTA)) or 0
    en_proceso = db.scalar(select(func.count()).select_from(OrdenTrabajo).where(OrdenTrabajo.estado == EstadoOTEnum.EN_PROCESO)) or 0
    listas_hoy = db.scalar(
        select(func.count()).select_from(OrdenTrabajo).where(
            OrdenTrabajo.estado == EstadoOTEnum.LISTA,
            OrdenTrabajo.fecha_termino == today,
        )
    ) or 0
    vehiculos_taller = db.scalar(
        select(func.count()).select_from(OrdenTrabajo).where(OrdenTrabajo.estado.in_([EstadoOTEnum.ABIERTA, EstadoOTEnum.EN_PROCESO]))
    ) or 0

    return {
        "ot_abiertas": abiertas,
        "ot_en_proceso": en_proceso,
        "ot_listas_hoy": listas_hoy,
        "vehiculos_en_taller": vehiculos_taller,
    }


def dashboard_status_summary(db: Session) -> list[dict[str, int | str]]:
    total = db.scalar(select(func.count()).select_from(OrdenTrabajo)) or 0
    rows = db.execute(
        select(OrdenTrabajo.estado, func.count())
        .group_by(OrdenTrabajo.estado)
        .order_by(OrdenTrabajo.estado)
    ).all()

    counts = {estado.value if estado else "SIN_ESTADO": cantidad for estado, cantidad in rows}
    ordered = [
        EstadoOTEnum.ABIERTA.value,
        EstadoOTEnum.EN_PROCESO.value,
        EstadoOTEnum.LISTA.value,
        EstadoOTEnum.FACTURADA.value,
        EstadoOTEnum.CERRADA.value,
    ]

    summary: list[dict[str, int | str]] = []
    for estado in ordered:
        cantidad = int(counts.get(estado, 0))
        porcentaje = int((cantidad / total) * 100) if total else 0
        summary.append({"estado": estado, "cantidad": cantidad, "porcentaje": porcentaje})
    return summary


def dashboard_recent_orders(db: Session) -> list[OrdenTrabajo]:
    return db.scalars(select(OrdenTrabajo).order_by(OrdenTrabajo.id.desc()).limit(5)).all()


def dashboard_master_counts(db: Session) -> dict[str, int]:
    return {
        "clientes": db.scalar(select(func.count()).select_from(Cliente)) or 0,
        "vehiculos": db.scalar(select(func.count()).select_from(Vehiculo)) or 0,
        "tecnicos": db.scalar(select(func.count()).select_from(Tecnico).where(Tecnico.activo.is_(True))) or 0,
        "repuestos": db.scalar(select(func.count()).select_from(Repuesto)) or 0,
    }


def dashboard_context(db: Session) -> dict:
    return {
        "kpis": dashboard_kpis(db),
        "status_summary": dashboard_status_summary(db),
        "recent_orders": dashboard_recent_orders(db),
        "master_counts": dashboard_master_counts(db),
    }


@router.get("/", response_class=HTMLResponse)
def dashboard_home(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    context = {
        "request": request,
        **base_context(),
        **dashboard_context(db),
    }
    return templates.TemplateResponse("pages/dashboard.html", context)


@router.get("/partials/dashboard-kpis", response_class=HTMLResponse)
def dashboard_kpis_partial(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    context = {
        "request": request,
        **dashboard_context(db),
    }
    return templates.TemplateResponse("components/dashboard_overview.html", context)
