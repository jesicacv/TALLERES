from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base

if TYPE_CHECKING:
    from app.models.ot_repuestos import OTRepuesto


class Repuesto(Base):
    __tablename__ = "repuestos"

    codigo: Mapped[str] = mapped_column(String(40), primary_key=True)
    nombre: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    precio_costo: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    precio_venta: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    stock_actual: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")

    items_ot: Mapped[list[OTRepuesto]] = relationship(back_populates="repuesto")
