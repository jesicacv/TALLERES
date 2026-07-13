from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from passlib.context import CryptContext
from sqlalchemy import select

from app.models.usuario import Permiso, Rol, RolPermiso, Usuario, UsuarioRol
from config.settings import DEFAULT_ADMIN_PASSWORD, settings
from database.base import SessionLocal

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ROLES_BASE = {
    "ADMIN": "Acceso total al sistema",
    "SUPERVISOR": "Supervisa operaciones del taller",
    "RECEPCIONISTA": "Gestiona ingreso y seguimiento de ordenes",
    "TECNICO": "Consulta y ejecuta trabajos asignados",
}

PERMISOS_BASE = [
    ("dashboard.ver", "dashboard", "Ver dashboard general"),
    ("clientes.ver", "clientes", "Ver clientes"),
    ("clientes.crear", "clientes", "Crear clientes"),
    ("clientes.editar", "clientes", "Editar clientes"),
    ("vehiculos.ver", "vehiculos", "Ver vehiculos"),
    ("vehiculos.crear", "vehiculos", "Crear vehiculos"),
    ("vehiculos.editar", "vehiculos", "Editar vehiculos"),
    ("tecnicos.ver", "tecnicos", "Ver tecnicos"),
    ("repuestos.ver", "repuestos", "Ver repuestos"),
    ("ordenes.ver", "ordenes_trabajo", "Ver ordenes de trabajo"),
    ("ordenes.crear", "ordenes_trabajo", "Crear ordenes de trabajo"),
    ("ordenes.editar", "ordenes_trabajo", "Editar ordenes de trabajo"),
    ("usuarios.ver", "usuarios", "Ver usuarios del sistema"),
    ("roles.ver", "roles", "Ver roles y permisos"),
]

ADMIN_USUARIO = {
    "username": settings.admin_web_user,
    "email": "admin@taller.local",
    "password": settings.admin_web_password,
    "nombre_completo": "Administrador General",
}

# Si la clave viene del .env (elegida por quien despliega) no tiene sentido forzar el cambio;
# solo se fuerza cuando quedo la clave debil por defecto.
FORZAR_CAMBIO_PASSWORD = settings.admin_web_password == DEFAULT_ADMIN_PASSWORD


def get_or_create_roles(session) -> dict[str, Rol]:
    roles: dict[str, Rol] = {}

    for nombre, descripcion in ROLES_BASE.items():
        role = session.scalar(select(Rol).where(Rol.nombre == nombre))
        if role is None:
            role = Rol(nombre=nombre, descripcion=descripcion)
            session.add(role)
            session.flush()
        roles[nombre] = role

    return roles


def get_or_create_permisos(session) -> list[Permiso]:
    permisos: list[Permiso] = []

    for codigo, modulo, descripcion in PERMISOS_BASE:
        permiso = session.scalar(select(Permiso).where(Permiso.codigo == codigo))
        if permiso is None:
            permiso = Permiso(codigo=codigo, modulo=modulo, descripcion=descripcion)
            session.add(permiso)
            session.flush()
        permisos.append(permiso)

    return permisos


def assign_admin_permissions(session, admin_role: Rol, permisos: list[Permiso]) -> None:
    for permiso in permisos:
        exists = session.scalar(
            select(RolPermiso).where(
                RolPermiso.rol_id == admin_role.id,
                RolPermiso.permiso_id == permiso.id,
            )
        )
        if exists is None:
            session.add(RolPermiso(rol_id=admin_role.id, permiso_id=permiso.id))


def get_or_create_admin(session, admin_role: Rol) -> Usuario:
    usuario = session.scalar(select(Usuario).where(Usuario.username == ADMIN_USUARIO["username"]))
    if usuario is None:
        usuario = Usuario(
            username=ADMIN_USUARIO["username"],
            email=ADMIN_USUARIO["email"],
            password_hash=pwd_context.hash(ADMIN_USUARIO["password"]),
            nombre_completo=ADMIN_USUARIO["nombre_completo"],
            activo=True,
            debe_cambiar_password=FORZAR_CAMBIO_PASSWORD,
        )
        session.add(usuario)
        session.flush()

    assigned = session.scalar(
        select(UsuarioRol).where(
            UsuarioRol.usuario_id == usuario.id,
            UsuarioRol.rol_id == admin_role.id,
        )
    )
    if assigned is None:
        session.add(UsuarioRol(usuario_id=usuario.id, rol_id=admin_role.id))

    return usuario


def run_seed() -> None:
    with SessionLocal() as session:
        roles = get_or_create_roles(session)
        permisos = get_or_create_permisos(session)
        assign_admin_permissions(session, roles["ADMIN"], permisos)
        admin = get_or_create_admin(session, roles["ADMIN"])
        session.commit()

        print("Seed OK")
        print(f"Roles base: {len(roles)}")
        print(f"Permisos base: {len(permisos)}")
        origen = "default (Admin123!)" if FORZAR_CAMBIO_PASSWORD else "ADMIN_WEB_PASSWORD del .env"
        print(f"Usuario admin: {admin.username} (clave: {origen})")


if __name__ == "__main__":
    run_seed()
