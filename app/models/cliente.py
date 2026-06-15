from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base

if TYPE_CHECKING:
    from app.models.orden_trabajo import OrdenTrabajo
    from app.models.vehiculo import Vehiculo


class Cliente(Base):
    __tablename__ = "clientes"

    rut: Mapped[str] = mapped_column(String(20), primary_key=True)
    nombre: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    direccion: Mapped[str | None] = mapped_column(String(255))
    ciudad: Mapped[str | None] = mapped_column(String(100))
    comuna: Mapped[str | None] = mapped_column(String(100))
    fono_particular: Mapped[str | None] = mapped_column(String(30))
    fono_oficina: Mapped[str | None] = mapped_column(String(30))
    celular: Mapped[str | None] = mapped_column(String(30))
    email: Mapped[str | None] = mapped_column(String(150), index=True)
    forma_pago_default: Mapped[str | None] = mapped_column(String(50))

    vehiculos: Mapped[list[Vehiculo]] = relationship(back_populates="cliente")
    ordenes_trabajo: Mapped[list[OrdenTrabajo]] = relationship(back_populates="cliente")
