from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy import delete, select

from app.core.security import hash_password
from app.models.usuario import IntentoLogin, Sesion, Usuario
from app.services.auth_service import authenticate_user, get_user_from_token, logout_session
from database.base import SessionLocal


class AuthSessionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.suffix = uuid4().hex[:8].lower()
        self.username = f"sess_{self.suffix}"
        self.password = "SessPass123!"
        with SessionLocal() as db:
            user = Usuario(
                username=self.username,
                email=f"{self.username}@test.local",
                password_hash=hash_password(self.password),
                nombre_completo="Session Tester",
                activo=True,
                debe_cambiar_password=False,
            )
            db.add(user)
            db.commit()
            self.user_id = user.id

    def tearDown(self) -> None:
        with SessionLocal() as db:
            db.execute(delete(Sesion).where(Sesion.usuario_id == self.user_id))
            db.execute(delete(IntentoLogin).where(IntentoLogin.username_intento == self.username))
            db.execute(delete(Usuario).where(Usuario.id == self.user_id))
            db.commit()

    def test_login_valido_y_resolucion_de_token(self) -> None:
        with SessionLocal() as db:
            user, token = authenticate_user(db, self.username, self.password, "1.2.3.4")
            self.assertEqual(user.id, self.user_id)
            resolved = get_user_from_token(db, token.access_token)
            self.assertEqual(resolved.id, self.user_id)

    def test_password_incorrecta_no_crea_sesion(self) -> None:
        with SessionLocal() as db:
            with self.assertRaises(HTTPException) as ctx:
                authenticate_user(db, self.username, "claveMala", "1.2.3.4")
            self.assertEqual(ctx.exception.status_code, 401)
            sesiones = db.scalars(select(Sesion).where(Sesion.usuario_id == self.user_id)).all()
            self.assertEqual(len(sesiones), 0)
            intentos = db.scalars(
                select(IntentoLogin).where(
                    IntentoLogin.username_intento == self.username,
                    IntentoLogin.exitoso.is_(False),
                )
            ).all()
            self.assertEqual(len(intentos), 1)

    def test_sesion_expirada_es_rechazada(self) -> None:
        with SessionLocal() as db:
            _, token = authenticate_user(db, self.username, self.password, "1.2.3.4")
            sesion = db.scalars(select(Sesion).where(Sesion.usuario_id == self.user_id)).one()
            sesion.expira_en = datetime.now(timezone.utc) - timedelta(minutes=1)
            db.commit()

            with self.assertRaises(HTTPException) as ctx:
                get_user_from_token(db, token.access_token)
            self.assertEqual(ctx.exception.status_code, 401)

            db.refresh(sesion)
            self.assertFalse(sesion.activa)  # quedo marcada inactiva

    def test_sesion_inactiva_es_rechazada(self) -> None:
        with SessionLocal() as db:
            _, token = authenticate_user(db, self.username, self.password, "1.2.3.4")
            sesion = db.scalars(select(Sesion).where(Sesion.usuario_id == self.user_id)).one()
            sesion.activa = False
            db.commit()

            with self.assertRaises(HTTPException) as ctx:
                get_user_from_token(db, token.access_token)
            self.assertEqual(ctx.exception.status_code, 401)

    def test_logout_invalida_la_sesion(self) -> None:
        with SessionLocal() as db:
            _, token = authenticate_user(db, self.username, self.password, "1.2.3.4")
            self.assertEqual(get_user_from_token(db, token.access_token).id, self.user_id)

            logout_session(db, token.access_token)

            with self.assertRaises(HTTPException) as ctx:
                get_user_from_token(db, token.access_token)
            self.assertEqual(ctx.exception.status_code, 401)

    def test_token_malformado_es_rechazado(self) -> None:
        with SessionLocal() as db:
            with self.assertRaises(ValueError):
                get_user_from_token(db, "esto-no-es-un-jwt")


if __name__ == "__main__":
    unittest.main()
