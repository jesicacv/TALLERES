from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Enum, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.enums import TipoItemOTEnum
from database.base import Base

if TYPE_CHECKING:
    from app.models.orden_trabajo import OrdenTrabajo
    from app.models.repuesto import Repuesto


class OTRepuesto(Base):
    __tablename__ = "ot_repuestos"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    ot_id: Mapped[int] = mapped_column(ForeignKey("ordenes_trabajo.id"), nullable=False, index=True)
    repuesto_codigo: Mapped[str | None] = mapped_column(ForeignKey("repuestos.codigo"), index=True)
    descripcion: Mapped[str] = mapped_column(Text, nullable=False)
    cantidad: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, default=1)
    precio_costo_unitario: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    precio_venta_unitario: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    descuento_pct: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, default=0, server_default="0")
    es_siniestro: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    tipo: Mapped[TipoItemOTEnum] = mapped_column(Enum(TipoItemOTEnum, name="tipo_item_ot_enum"), nullable=False)

    orden_trabajo: Mapped[OrdenTrabajo] = relationship(back_populates="repuestos")
    repuesto: Mapped[Repuesto | None] = relationship(back_populates="items_ot")
