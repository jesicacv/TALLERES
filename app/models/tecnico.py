from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base

if TYPE_CHECKING:
    from app.models.ot_mano_obra import OTManoObra


class Tecnico(Base):
    __tablename__ = "tecnicos"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    codigo: Mapped[str] = mapped_column(String(30), nullable=False, unique=True, index=True)
    nombre: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")

    mano_obra: Mapped[list[OTManoObra]] = relationship(back_populates="tecnico")
