from __future__ import annotations

import unittest
from uuid import uuid4

from sqlalchemy import delete, select

from app.models.usuario import Permiso, Rol, RolPermiso, Usuario, UsuarioRol
from app.routes.seguridad import _sync_role_permisos, _sync_user_roles
from database.base import SessionLocal


class RolePermisoSyncTests(unittest.TestCase):
    """Prueba la sincronizacion de set roles<->permisos y usuario<->roles.

    Nota: SessionLocal usa expire_on_commit=False, asi que tras cada commit se llama
    expire_all() para emular el patron real de 'una sesion por request' (la funcion bajo
    prueba relee rol.permisos fresco) y las aserciones consultan las tablas hijas directo.
    """

    def setUp(self) -> None:
        self.suffix = uuid4().hex[:8].lower()

    def _permiso_ids(self, db) -> set[int]:
        return set(db.scalars(select(RolPermiso.permiso_id).where(RolPermiso.rol_id == self.rol_id)).all())

    def test_sync_role_permisos_agrega_y_quita(self) -> None:
        with SessionLocal() as db:
            rol = Rol(nombre=f"ROL_{self.suffix}")
            db.add(rol)
            db.flush()
            self.rol_id = rol.id
            perms = [Permiso(codigo=f"perm_{i}_{self.suffix}", modulo="tests") for i in range(3)]
            db.add_all(perms)
            db.flush()
            pid = [p.id for p in perms]

            try:
                _sync_role_permisos(db, rol, [pid[0], pid[1]])
                db.commit()
                db.expire_all()
                self.assertEqual(self._permiso_ids(db), {pid[0], pid[1]})

                # cambia el set: saca p0, agrega p2, mantiene p1
                rol = db.get(Rol, self.rol_id)
                _sync_role_permisos(db, rol, [pid[1], pid[2]])
                db.commit()
                db.expire_all()
                self.assertEqual(self._permiso_ids(db), {pid[1], pid[2]})

                # lista vacia => sin permisos
                rol = db.get(Rol, self.rol_id)
                _sync_role_permisos(db, rol, [])
                db.commit()
                db.expire_all()
                self.assertEqual(self._permiso_ids(db), set())

                # ids inexistentes se ignoran (no crashea, no agrega)
                rol = db.get(Rol, self.rol_id)
                _sync_role_permisos(db, rol, [999_000_001, 999_000_002])
                db.commit()
                db.expire_all()
                self.assertEqual(self._permiso_ids(db), set())
            finally:
                db.execute(delete(RolPermiso).where(RolPermiso.rol_id == self.rol_id))
                db.execute(delete(Permiso).where(Permiso.id.in_(pid)))
                db.execute(delete(Rol).where(Rol.id == self.rol_id))
                db.commit()

    def test_sync_user_roles_agrega_y_quita(self) -> None:
        with SessionLocal() as db:
            usuario = Usuario(
                username=f"u_{self.suffix}",
                email=f"u_{self.suffix}@test.local",
                password_hash="x",
                nombre_completo="Sync Tester",
                activo=True,
                debe_cambiar_password=False,
            )
            db.add(usuario)
            db.flush()
            uid = usuario.id
            roles = [Rol(nombre=f"R{i}_{self.suffix}") for i in range(3)]
            db.add_all(roles)
            db.flush()
            rid = [r.id for r in roles]

            def current() -> set[int]:
                return set(db.scalars(select(UsuarioRol.rol_id).where(UsuarioRol.usuario_id == uid)).all())

            try:
                _sync_user_roles(db, usuario, [rid[0], rid[1]])
                db.commit()
                db.expire_all()
                self.assertEqual(current(), {rid[0], rid[1]})

                usuario = db.get(Usuario, uid)
                _sync_user_roles(db, usuario, [rid[2]])
                db.commit()
                db.expire_all()
                self.assertEqual(current(), {rid[2]})

                usuario = db.get(Usuario, uid)
                _sync_user_roles(db, usuario, [])
                db.commit()
                db.expire_all()
                self.assertEqual(current(), set())
            finally:
                db.execute(delete(UsuarioRol).where(UsuarioRol.usuario_id == uid))
                db.execute(delete(Rol).where(Rol.id.in_(rid)))
                db.execute(delete(Usuario).where(Usuario.id == uid))
                db.commit()


if __name__ == "__main__":
    unittest.main()
