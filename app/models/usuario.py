from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from database.base import Base

if TYPE_CHECKING:
    from app.models.auditoria import Auditoria
    from app.models.orden_trabajo import OrdenTrabajo


class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    email: Mapped[str] = mapped_column(String(150), nullable=False, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    nombre_completo: Mapped[str] = mapped_column(String(150), nullable=False)
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    debe_cambiar_password: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    ultimo_acceso: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    ordenes_recepcionadas: Mapped[list[OrdenTrabajo]] = relationship(back_populates="recepcionista")
    roles: Mapped[list[UsuarioRol]] = relationship(back_populates="usuario", cascade="all, delete-orphan")
    auditorias: Mapped[list[Auditoria]] = relationship(back_populates="usuario")
    sesiones: Mapped[list[Sesion]] = relationship(back_populates="usuario", cascade="all, delete-orphan")


class Rol(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(80), nullable=False, unique=True, index=True)
    descripcion: Mapped[str | None] = mapped_column(Text)

    usuarios: Mapped[list[UsuarioRol]] = relationship(back_populates="rol", cascade="all, delete-orphan")
    permisos: Mapped[list[RolPermiso]] = relationship(back_populates="rol", cascade="all, delete-orphan")


class Permiso(Base):
    __tablename__ = "permisos"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    codigo: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    modulo: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    descripcion: Mapped[str | None] = mapped_column(Text)

    roles: Mapped[list[RolPermiso]] = relationship(back_populates="permiso", cascade="all, delete-orphan")


class UsuarioRol(Base):
    __tablename__ = "usuarios_roles"

    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), primary_key=True)
    rol_id: Mapped[int] = mapped_column(ForeignKey("roles.id"), primary_key=True)

    usuario: Mapped[Usuario] = relationship(back_populates="roles")
    rol: Mapped[Rol] = relationship(back_populates="usuarios")


class RolPermiso(Base):
    __tablename__ = "roles_permisos"

    rol_id: Mapped[int] = mapped_column(ForeignKey("roles.id"), primary_key=True)
    permiso_id: Mapped[int] = mapped_column(ForeignKey("permisos.id"), primary_key=True)

    rol: Mapped[Rol] = relationship(back_populates="permisos")
    permiso: Mapped[Permiso] = relationship(back_populates="roles")


class Sesion(Base):
    __tablename__ = "sesiones"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), nullable=False, index=True)
    token_hash: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    ip_origen: Mapped[str | None] = mapped_column(String(45))
    expira_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    activa: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")

    usuario: Mapped[Usuario] = relationship(back_populates="sesiones")


class IntentoLogin(Base):
    __tablename__ = "intentos_login"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username_intento: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    ip_origen: Mapped[str | None] = mapped_column(String(45))
    exitoso: Mapped[bool] = mapped_column(Boolean, nullable=False)
    fecha: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
