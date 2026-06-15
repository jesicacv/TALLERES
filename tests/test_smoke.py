from __future__ import annotations

import unittest
from datetime import date, datetime, timezone
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from app.core.security import hash_password
from app.main import app
from app.models.auditoria import Auditoria
from app.models.cliente import Cliente
from app.models.orden_trabajo import OrdenTrabajo
from app.models.ot_checklist import OTChecklist
from app.models.ot_mano_obra import OTManoObra
from app.models.ot_repuestos import OTRepuesto
from app.models.repuesto import Repuesto
from app.models.tecnico import Tecnico
from app.models.usuario import IntentoLogin, Permiso, Sesion, Usuario
from app.models.vehiculo import Vehiculo
from database.base import SessionLocal


class AppSmokeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)
        self.started_at = datetime.now(timezone.utc)
        self.suffix = uuid4().hex[:8].upper()
        self.created = {
            "clientes": [],
            "vehiculos": [],
            "tecnicos": [],
            "repuestos": [],
            "permisos": [],
            "ordenes": [],
        }

        # Las paginas web exigen sesion (ID-T03). Creamos un usuario de prueba sin
        # password-change pendiente y autenticamos el cliente via la cookie de sesion.
        self.test_username = f"smoke_{self.suffix.lower()}"
        self.test_password = "SmokePass123!"
        with SessionLocal() as db:
            user = Usuario(
                username=self.test_username,
                email=f"{self.test_username}@test.local",
                password_hash=hash_password(self.test_password),
                nombre_completo="Smoke Tester",
                activo=True,
                debe_cambiar_password=False,
            )
            db.add(user)
            db.commit()
            self.test_user_id = user.id

        login = self.client.post(
            "/login",
            data={"username": self.test_username, "password": self.test_password},
        )
        self.assertEqual(login.status_code, 200)

    def tearDown(self) -> None:
        with SessionLocal() as db:
            ot_ids = list(
                db.scalars(
                    select(OrdenTrabajo.id).where(OrdenTrabajo.numero_ot.in_(self.created["ordenes"]))
                ).all()
            )

            db.execute(delete(OTChecklist).where(OTChecklist.ot_id.in_(ot_ids)))
            db.execute(delete(OTManoObra).where(OTManoObra.ot_id.in_(ot_ids)))
            db.execute(delete(OTRepuesto).where(OTRepuesto.ot_id.in_(ot_ids)))
            db.execute(delete(OrdenTrabajo).where(OrdenTrabajo.numero_ot.in_(self.created["ordenes"])))
            db.execute(delete(Vehiculo).where(Vehiculo.patente.in_(self.created["vehiculos"])))
            db.execute(delete(Cliente).where(Cliente.rut.in_(self.created["clientes"])))
            db.execute(delete(Tecnico).where(Tecnico.codigo.in_(self.created["tecnicos"])))
            db.execute(delete(Repuesto).where(Repuesto.codigo.in_(self.created["repuestos"])))
            db.execute(delete(Permiso).where(Permiso.codigo.in_(self.created["permisos"])))
            db.execute(
                delete(Auditoria).where(
                    Auditoria.ip_origen == "testclient",
                    Auditoria.fecha >= self.started_at,
                )
            )
            # El usuario de prueba se borra al final: la auditoria que lo referencia (FK)
            # ya fue eliminada arriba.
            db.execute(delete(Sesion).where(Sesion.usuario_id == self.test_user_id))
            db.execute(delete(IntentoLogin).where(IntentoLogin.username_intento == self.test_username))
            db.execute(delete(Usuario).where(Usuario.id == self.test_user_id))
            db.commit()

    def test_system_and_dashboard_endpoints(self) -> None:
        root = self.client.get("/")
        partial = self.client.get("/partials/dashboard-kpis", headers={"HX-Request": "true"})
        api = self.client.get("/api")
        health = self.client.get("/system/health")
        version = self.client.get("/system/version")

        self.assertEqual(root.status_code, 200)
        self.assertIn("Resumen del Taller", root.text)
        self.assertEqual(partial.status_code, 200)
        self.assertIn("Actividad Reciente", partial.text)
        self.assertEqual(api.status_code, 200)
        self.assertEqual(api.json()["message"], "API Taller Mecanico activa")
        self.assertEqual(health.status_code, 200)
        self.assertEqual(health.json()["status"], "ok")
        self.assertEqual(version.status_code, 200)
        self.assertIn("version", version.json())

    def test_auth_flow_writes_audit_events(self) -> None:
        login = self.client.post("/auth/login", json={"username": "admin", "password": "Admin123!"})
        self.assertEqual(login.status_code, 200)

        token = login.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        me = self.client.get("/auth/me", headers=headers)
        logout = self.client.post("/auth/logout", headers=headers)
        audit_page = self.client.get("/seguridad/auditoria")

        self.assertEqual(me.status_code, 200)
        self.assertEqual(logout.status_code, 200)
        self.assertEqual(audit_page.status_code, 200)
        self.assertIn("Auditoria", audit_page.text)

        with SessionLocal() as db:
            auth_rows = db.scalars(
                select(Auditoria)
                .where(Auditoria.modulo == "AUTH", Auditoria.ip_origen == "testclient", Auditoria.fecha >= self.started_at)
                .order_by(Auditoria.id.desc())
            ).all()

        acciones = {row.accion for row in auth_rows}
        self.assertIn("LOGIN", acciones)
        self.assertIn("LOGOUT", acciones)

    def test_operational_flow_writes_audit_events(self) -> None:
        rut = f"T{self.suffix}"
        patente = f"P{self.suffix[:6]}"
        tecnico = f"TEC{self.suffix}"
        repuesto = f"REP{self.suffix}"
        permiso = f"perm.temp.{self.suffix.lower()}"
        numero_ot = f"OT-{self.suffix}"

        self.created["clientes"].append(rut)
        self.created["vehiculos"].append(patente)
        self.created["tecnicos"].append(tecnico)
        self.created["repuestos"].append(repuesto)
        self.created["permisos"].append(permiso)
        self.created["ordenes"].append(numero_ot)

        self.assertEqual(self.client.post("/maestros/clientes/create", data={"rut": rut, "nombre": "Cliente Test"}).status_code, 200)
        self.assertEqual(
            self.client.post(
                "/maestros/vehiculos/create",
                data={"patente": patente, "cliente_rut": rut, "marca": "Mazda", "modelo": "2", "tipo": "AUTO"},
            ).status_code,
            200,
        )
        self.assertEqual(
            self.client.post("/maestros/tecnicos/create", data={"codigo": tecnico, "nombre": "Tecnico Test", "activo": "on"}).status_code,
            200,
        )
        self.assertEqual(
            self.client.post(
                "/maestros/repuestos/create",
                data={"codigo": repuesto, "nombre": "Filtro Test", "precio_costo": "12", "precio_venta": "18", "stock_actual": "4"},
            ).status_code,
            200,
        )
        self.assertEqual(
            self.client.post(
                "/seguridad/permisos/create",
                data={"codigo": permiso, "modulo": "tests", "descripcion": "permiso temporal"},
            ).status_code,
            200,
        )

        with SessionLocal() as db:
            tecnico_id = db.scalar(select(Tecnico.id).where(Tecnico.codigo == tecnico))

        self.assertIsNotNone(tecnico_id)
        self.assertEqual(
            self.client.post(
                "/movimientos/ordenes-trabajo/create",
                data={
                    "numero_ot": numero_ot,
                    "patente": patente,
                    "recepcionista_id": "1",
                    "fecha_ingreso": str(date.today()),
                    "estado": "ABIERTA",
                },
            ).status_code,
            200,
        )

        with SessionLocal() as db:
            ot_id = db.scalar(select(OrdenTrabajo.id).where(OrdenTrabajo.numero_ot == numero_ot))

        self.assertIsNotNone(ot_id)
        self.assertEqual(
            self.client.post(
                f"/movimientos/ordenes-trabajo/{ot_id}/mano-obra/create",
                data={
                    "tecnico_id": str(tecnico_id),
                    "descripcion_trabajo": "Diagnostico inicial",
                    "horas": "1.5",
                    "precio_unitario": "25",
                    "descuento_pct": "0",
                    "bonificacion": "0",
                },
            ).status_code,
            200,
        )
        self.assertEqual(
            self.client.post(
                f"/movimientos/ordenes-trabajo/{ot_id}/repuestos/create",
                data={"repuesto_codigo": repuesto, "descripcion": "Filtro Test", "cantidad": "1", "tipo": "REPUESTO"},
            ).status_code,
            200,
        )
        self.assertEqual(
            self.client.post(
                f"/movimientos/ordenes-trabajo/{ot_id}/checklist/create",
                data={"item": "Revision visual", "observacion": "Sin novedades"},
            ).status_code,
            200,
        )

        expected = {
            "MAESTROS_CLIENTES": rut,
            "MAESTROS_VEHICULOS": patente,
            "MAESTROS_TECNICOS": tecnico,
            "MAESTROS_REPUESTOS": repuesto,
            "SEGURIDAD_PERMISOS": permiso,
            "MOVIMIENTOS_OT": numero_ot,
            "MOVIMIENTOS_MANO_OBRA": str(ot_id),
            "MOVIMIENTOS_REPUESTOS_OT": str(ot_id),
            "MOVIMIENTOS_CHECKLIST": str(ot_id),
        }

        with SessionLocal() as db:
            audit_rows = db.scalars(select(Auditoria).where(Auditoria.fecha >= self.started_at)).all()

        audited_pairs = {(row.modulo, row.entidad_id) for row in audit_rows}
        for modulo, entidad_id in expected.items():
            self.assertIn((modulo, entidad_id), audited_pairs)

    def test_protected_pages_require_session(self) -> None:
        anon = TestClient(app)

        page = anon.get("/maestros/clientes", follow_redirects=False)
        self.assertEqual(page.status_code, 303)
        self.assertEqual(page.headers["location"], "/login")

        mutation = anon.post(
            "/maestros/clientes/create",
            data={"rut": "X", "nombre": "Y"},
            follow_redirects=False,
        )
        self.assertEqual(mutation.status_code, 303)
        self.assertEqual(mutation.headers["location"], "/login")

        self.assertEqual(anon.get("/login").status_code, 200)

    def test_password_change_gate_redirects(self) -> None:
        username = f"pw_{self.suffix.lower()}"
        password = "TempPass123!"
        with SessionLocal() as db:
            user = Usuario(
                username=username,
                email=f"{username}@test.local",
                password_hash=hash_password(password),
                nombre_completo="PW Tester",
                activo=True,
                debe_cambiar_password=True,
            )
            db.add(user)
            db.commit()
            uid = user.id

        try:
            client = TestClient(app)
            login = client.post(
                "/login",
                data={"username": username, "password": password},
                follow_redirects=False,
            )
            self.assertEqual(login.status_code, 303)
            self.assertEqual(login.headers["location"], "/cambiar-password")

            page = client.get("/maestros/clientes", follow_redirects=False)
            self.assertEqual(page.status_code, 303)
            self.assertEqual(page.headers["location"], "/cambiar-password")
        finally:
            with SessionLocal() as db:
                db.execute(delete(Auditoria).where(Auditoria.usuario_id == uid))
                db.execute(delete(Sesion).where(Sesion.usuario_id == uid))
                db.execute(delete(IntentoLogin).where(IntentoLogin.username_intento == username))
                db.execute(delete(Usuario).where(Usuario.id == uid))
                db.commit()


if __name__ == "__main__":
    unittest.main()