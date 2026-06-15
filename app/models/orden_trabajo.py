from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Date, Enum, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.enums import EstadoOTEnum
from database.base import Base

if TYPE_CHECKING:
    from app.models.cliente import Cliente
    from app.models.ot_checklist import OTChecklist
    from app.models.ot_mano_obra import OTManoObra
    from app.models.ot_repuestos import OTRepuesto
    from app.models.usuario import Usuario
    from app.models.vehiculo import Vehiculo


class OrdenTrabajo(Base):
    __tablename__ = "ordenes_trabajo"
    __table_args__ = (
        Index("ix_ordenes_trabajo_numero_ot", "numero_ot"),
        Index("ix_ordenes_trabajo_estado", "estado"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    numero_ot: Mapped[str] = mapped_column(String(30), nullable=False, unique=True)
    patente: Mapped[str] = mapped_column(ForeignKey("vehiculos.patente"), nullable=False, index=True)
    cliente_rut: Mapped[str] = mapped_column(ForeignKey("clientes.rut"), nullable=False, index=True)
    recepcionista_id: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id"))
    fecha_ingreso: Mapped[date] = mapped_column(Date, nullable=False)
    fecha_prometida: Mapped[date | None] = mapped_column(Date)
    fecha_termino: Mapped[date | None] = mapped_column(Date)
    kms_ingreso: Mapped[int | None] = mapped_column(Integer)
    glosa_general: Mapped[str | None] = mapped_column(Text)
    forma_pago: Mapped[str | None] = mapped_column(String(50))
    estado: Mapped[EstadoOTEnum] = mapped_column(Enum(EstadoOTEnum, name="estado_ot_enum"), nullable=False)

    vehiculo: Mapped[Vehiculo] = relationship(back_populates="ordenes_trabajo")
    cliente: Mapped[Cliente] = relationship(back_populates="ordenes_trabajo")
    recepcionista: Mapped[Usuario | None] = relationship(back_populates="ordenes_recepcionadas")
    mano_obra: Mapped[list[OTManoObra]] = relationship(back_populates="orden_trabajo", cascade="all, delete-orphan")
    repuestos: Mapped[list[OTRepuesto]] = relationship(back_populates="orden_trabajo", cascade="all, delete-orphan")
    checklist_items: Mapped[list[OTChecklist]] = relationship(back_populates="orden_trabajo", cascade="all, delete-orphan")
