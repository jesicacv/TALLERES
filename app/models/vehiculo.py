from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.enums import TipoVehiculoEnum
from database.base import Base

if TYPE_CHECKING:
    from app.models.cliente import Cliente
    from app.models.orden_trabajo import OrdenTrabajo


class Vehiculo(Base):
    __tablename__ = "vehiculos"

    patente: Mapped[str] = mapped_column(String(12), primary_key=True)
    cliente_rut: Mapped[str] = mapped_column(ForeignKey("clientes.rut"), nullable=False, index=True)
    marca: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    modelo: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    sub_modelo: Mapped[str | None] = mapped_column(String(80))
    tipo: Mapped[TipoVehiculoEnum] = mapped_column(Enum(TipoVehiculoEnum, name="tipo_vehiculo_enum"), nullable=False)
    anio: Mapped[int | None] = mapped_column(Integer)
    color: Mapped[str | None] = mapped_column(String(50))
    chasis_vin: Mapped[str | None] = mapped_column(String(50), unique=True)

    cliente: Mapped[Cliente] = relationship(back_populates="vehiculos")
    ordenes_trabajo: Mapped[list[OrdenTrabajo]] = relationship(back_populates="vehiculo")
