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

## Dependencias a RECONCILIAR (declaradas en requirements.txt, sin uso directo en `app/`)

| Lib | Pin | Situación | Acción sugerida |
|---|---|---|---|
| `httpx` | 0.25.2 | **Uso legítimo indirecto:** lo requiere `fastapi.testclient.TestClient` (suite de tests). | Mantener; marcar como dependencia de test. |
| `aiofiles` | 23.2.1 | **Sin uso** en el código actual (`grep` sin hits en `app/`). | Confirmar si es para una feature futura (uploads/PDF); si no, remover (requiere OK — ver R "no tocar requirements sin aprobación"). |
| `email-validator` | 2.2.0 | **Sin uso directo:** los schemas usan `str`, no `EmailStr`. Entra como dep de validación de email de Pydantic. | Mantener solo si se planea usar `EmailStr`; documentar o remover. |

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
