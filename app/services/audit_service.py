from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any
from uuid import UUID

from fastapi import Request
from sqlalchemy.inspection import inspect as sa_inspect
from sqlalchemy.orm import Session

from app.models.auditoria import Auditoria


def _serialize_value(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, UUID):
        return str(value)
    return value


def model_to_dict(instance: Any) -> dict[str, Any]:
    mapper = sa_inspect(instance.__class__)
    return {
        column.key: _serialize_value(getattr(instance, column.key))
        for column in mapper.columns
    }


def log_audit(
    db: Session,
    request: Request | None,
    *,
    accion: str,
    modulo: str,
    entidad_id: str | None = None,
    datos_anteriores: dict[str, Any] | None = None,
    datos_nuevos: dict[str, Any] | None = None,
    usuario_id: int | None = None,
) -> None:
    ip_origen = None
    if request is not None and request.client is not None:
        ip_origen = request.client.host

    db.add(
        Auditoria(
            usuario_id=usuario_id,
            accion=accion,
            modulo=modulo,
            entidad_id=entidad_id,
            datos_anteriores=datos_anteriores,
            datos_nuevos=datos_nuevos,
            ip_origen=ip_origen,
        )
    )