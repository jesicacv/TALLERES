from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base

if TYPE_CHECKING:
    from app.models.orden_trabajo import OrdenTrabajo


class OTChecklist(Base):
    __tablename__ = "ot_checklist"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    ot_id: Mapped[int] = mapped_column(ForeignKey("ordenes_trabajo.id"), nullable=False, index=True)
    item: Mapped[str] = mapped_column(String(120), nullable=False)
    completado: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    observacion: Mapped[str | None] = mapped_column(Text)

    orden_trabajo: Mapped[OrdenTrabajo] = relationship(back_populates="checklist_items")
