from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Numeric, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base

if TYPE_CHECKING:
    from app.models.orden_trabajo import OrdenTrabajo
    from app.models.tecnico import Tecnico


class OTManoObra(Base):
    __tablename__ = "ot_mano_obra"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    ot_id: Mapped[int] = mapped_column(ForeignKey("ordenes_trabajo.id"), nullable=False, index=True)
    tecnico_id: Mapped[int] = mapped_column(ForeignKey("tecnicos.id"), nullable=False, index=True)
    descripcion_trabajo: Mapped[str] = mapped_column(Text, nullable=False)
    horas: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    precio_unitario: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    descuento_pct: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, default=0, server_default="0")
    bonificacion: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0, server_default="0")
    total_neto: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    total_con_impuesto: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)

    orden_trabajo: Mapped[OrdenTrabajo] = relationship(back_populates="mano_obra")
    tecnico: Mapped[Tecnico] = relationship(back_populates="mano_obra")
