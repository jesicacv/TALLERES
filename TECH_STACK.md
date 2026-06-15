# TECH_STACK.md — TALLERES

> Stack declarado vs. usado. Regla del harness: toda dependencia en `requirements.txt`
> debe tener un uso legítimo y trazable; toda tecnología del stack debe estar declarada.
> Generado contra el código y `requirements.txt` el 2026-06-15.

## Lo que SE USA (núcleo)

| Tecnología | Versión (pin) | Rol en el proyecto |
|---|---|---|
| Python | 3.11.2 | Lenguaje (venv en `venv/`) |
| FastAPI | 0.104.1 | Framework web / API (`app/main.py`, 6 routers) |
| uvicorn[standard] | 0.24.0 | Servidor ASGI (dev y prod) |
| SQLAlchemy | 2.0.23 | ORM, sesión `get_db()` (`database/base.py`) |
| psycopg2-binary | 2.9.9 | Driver PostgreSQL |
| alembic | 1.13.0 | Migraciones (`alembic/versions/`) |
| Jinja2 | 3.1.2 | Templates server-side (`app/templates/`) |
| pydantic | 2.5.0 | Validación / schemas (`app/schemas/`, modelos de respuesta) |
| pydantic-settings | 2.1.0 | Carga de config desde `.env` (`config/settings.py`) |
| python-jose[cryptography] | 3.3.0 | Firma/verificación JWT (`app/core/security.py`) |
| passlib[bcrypt] | 1.7.4 | Hash de contraseñas (`security.py`, `seed.py`) |
| bcrypt | 4.0.1 | Backend de hashing para passlib |
| python-dotenv | 1.0.0 | Carga de `.env` (soporte de pydantic-settings / tooling) |
| python-multipart | 0.0.9 | Parseo de `Form(...)` (todos los POST de UI) |

### Frontend (sin gestor de paquetes, vía CDN)

- **HTMX 1.9.12** — `unpkg.com/htmx.org@1.9.12` (en `templates/base/layout.html`).
- **Tailwind CSS** — `cdn.tailwindcss.com` con `tallerGreen=#1B6B5A` / `tallerBlue=#1B3F7A`.
- CSS propio en `app/static/css/app.css`. **Sin** Alpine.js, **sin** build step, **sin** JS a mano (alineado con `PromptModelo §2`).

### Dependencia de test

| Lib | Pin | Rol |
|---|---|---|
| `httpx` | 0.25.2 | Requerido por `fastapi.testclient.TestClient` (`tests/test_smoke.py`). Marcado como dep de test en `requirements.txt`. |

## Reconciliación de dependencias ([ID-T06], resuelto 2026-06-15)

- **`aiofiles`** y **`email-validator`** se **removieron** de `requirements.txt` y del venv:
  sin uso en el código (grep sin hits en todo el repo) y sin reverse-deps (`pip show` →
  `Required-by` vacío). `email-validator` solo haría falta si se adoptara `EmailStr`
  (hoy los schemas usan `str`). `pip check` limpio y tests 5/5 tras la remoción.
- **`httpx`** se mantiene (necesario para los tests) y quedó anotado como tal.

> `matplotlib` / `aiosmtplib` mencionados en auditorías de otros proyectos Flex **NO**
> están en este `requirements.txt` — no aplican aquí.

## Pinning

Todas las dependencias están **fijadas con `==`** (cumple el checklist del harness).
Nota menor: `pydantic` está declarado explícitamente (bien), pese a ser además dep
transitiva de FastAPI.

## Entorno y base de datos

- **DB:** PostgreSQL. Conexión vía `DATABASE_URL` en `.env` (`config/settings.py`).
- **Esquema:** gestionado por Alembic (`alembic upgrade head`). Dos migraciones: schema inicial + `ot_checklist`.
- **Semilla:** `python -m database.seed` (roles, permisos, admin).
- **Deploy/uso:** interno, Windows. Lanzadores `lanzar_app.bat` y `run_dev.ps1` (uvicorn en `127.0.0.1:8000`).
- **Dos entornos virtuales en disco:** `venv/` (el que usan los lanzadores) y `.venv/`. Solo `venv/` está en `.gitignore` — ver `AUDIT_REPORT.md` [ID-T05].
