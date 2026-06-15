from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from database.base import Base

if TYPE_CHECKING:
    from app.models.usuario import Usuario


class Auditoria(Base):
    __tablename__ = "auditoria"
    __table_args__ = (Index("ix_auditoria_fecha", "fecha"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    usuario_id: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id"), index=True)
    accion: Mapped[str] = mapped_column(String(80), nullable=False)
    modulo: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    entidad_id: Mapped[str | None] = mapped_column(String(80), index=True)
    datos_anteriores: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    datos_nuevos: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    ip_origen: Mapped[str | None] = mapped_column(String(45))
    fecha: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    usuario: Mapped[Usuario | None] = relationship(back_populates="auditorias")
