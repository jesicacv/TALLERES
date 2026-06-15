# CLAUDE.md — TALLERES (Gestión de Taller Mecánico)

> Guía operativa para agentes (Claude Code / Antigravity) trabajando en este repo.
> Proyecto **Flex Consultora** — _"Donde el ERP no llega, Flex resuelve."_
> Especificación funcional canónica: [`PromptModelo_TallerMecanico.md`](PromptModelo_TallerMecanico.md).
> Estado del harness y deuda técnica: [`AUDIT_REPORT.md`](AUDIT_REPORT.md) · [`NEXT_STEPS.md`](NEXT_STEPS.md).

## 0. Idioma — TODO en español

**Toda la comunicación y el contenido de este proyecto va en español.** Esto incluye: las
respuestas al usuario, los mensajes de commit, los comentarios y docstrings del código, la
documentación (`.md`), los textos de UI y los mensajes de error/validación. Identificadores
de código (nombres de variables, funciones, rutas) pueden quedar en inglés si así está la
convención existente, pero todo lo legible por humanos se redacta en español.

## 1. Qué es esto

App web interna para administrar un taller mecánico: clientes y vehículos, órdenes de
trabajo (OT), mano de obra y repuestos por OT, checklist de ingreso, técnicos, y
seguridad (usuarios / roles / permisos / auditoría). La usan recepcionistas, técnicos,
supervisores y administradores.

## 2. Stack real (ver `TECH_STACK.md` para el detalle libs↔uso)

- **Lenguaje:** Python 3.11.2 (venv en `venv/`).
- **Backend:** FastAPI (server-side rendering, **no** SPA).
- **Frontend:** Jinja2 + **HTMX 1.9.12** (CDN) + **Tailwind CSS** (CDN `cdn.tailwindcss.com`). Sin JS adicional, sin Alpine, sin build step.
- **DB:** PostgreSQL vía **SQLAlchemy 2.0** (driver `psycopg2`).
- **Migraciones:** Alembic (`alembic/versions/`).
- **Auth:** JWT (`python-jose`) + hashing `passlib[bcrypt]`, con **sesiones server-side** en tabla `sesiones`.
- **Config:** `pydantic-settings` leyendo `.env`.

## 3. Estructura del proyecto

```
TALLERES/
├── main.py                 # shim: from app.main import app
├── app/
│   ├── main.py             # FastAPI app, CORS, monta /static, incluye routers
│   ├── core/
│   │   ├── security.py     # JWT encode/decode, hash/verify password, token_hash
│   │   └── templating.py   # Jinja2Templates + base_context()
│   ├── models/             # Modelos ORM SQLAlchemy (uno por entidad) + enums.py
│   ├── schemas/            # Schemas Pydantic v2 (hoy: solo auth.py)
│   ├── routes/             # Routers por dominio (web, auth, maestros, movimientos, seguridad, system)
│   ├── services/           # Lógica reutilizable (auth_service, audit_service)
│   ├── templates/          # base/, components/, pages/ (Jinja2)
│   └── static/css/app.css
├── config/settings.py      # Settings (pydantic-settings)
├── database/
│   ├── base.py             # engine, SessionLocal, Base, get_db()
│   └── seed.py             # roles/permisos base + usuario admin
├── alembic/                # migraciones
├── tests/                  # suite unittest: smoke, costos, seguridad-sync, auth-sessions
├── requirements.txt
├── lanzar_app.bat / run_dev.ps1   # lanzadores dev (Windows)
└── .env / .env.example
```

### Convención de capas (derivada del código, no de ADRs de otros proyectos)

- **`routes/`** orquesta: parsea `Form(...)`/query, llama a `db`/services, audita y
  responde (`TemplateResponse` para UI, `RedirectResponse(303)` tras mutación, o JSON
  para `/api`, `/system/*`, `/auth/*`).
- **`services/`** contiene lógica reutilizable / transversal (`auth_service`,
  `audit_service`). **No hay capa `repositories/`**: las consultas SQLAlchemy viven
  inline en los routers vía la `Session` de `get_db()`. Es el patrón vigente — respétalo;
  no introduzcas un ORM repo-layer sin acuerdo previo.
- **`models/`** = ORM SQLAlchemy. **`schemas/`** = Pydantic. Hoy casi todas las entradas
  son `Form(...)` HTML, por eso solo `auth` tiene schemas Pydantic. Si agregas endpoints
  JSON, define el schema en `app/schemas/`, no inline.

## 4. Cómo correr

```powershell
# 1) Activar venv del proyecto (el lanzador usa venv\Scripts\python.exe)
# 2) Levantar la app (recarga en caliente):
.\run_dev.ps1          # equivalente PowerShell de lanzar_app.bat
#   → http://127.0.0.1:8000   ·   /docs (OpenAPI)
```

Requiere un PostgreSQL accesible según `.env` y la base migrada + sembrada:

```powershell
.\venv\Scripts\python.exe -m alembic upgrade head     # crear/actualizar esquema
.\venv\Scripts\python.exe -m database.seed            # roles, permisos y admin
```

**Usuario semilla:** `admin` / `Admin123!` (con `debe_cambiar_password=True`).

## 5. Tests

La suite es **`unittest`** (no pytest), integración real contra la DB de `.env`:

```powershell
.\venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py" -v
```

Los tests crean datos con sufijo aleatorio y limpian en `tearDown` (incluida la
auditoría de `ip_origen == "testclient"`). **Necesitan DB viva y sembrada.** VS Code ya
tiene unittest configurado (`.vscode/settings.json`).

## 6. Patrones a respetar

- **Auditoría obligatoria en toda mutación.** Tras crear/editar/borrar, llamar
  `log_audit(db, request, accion=..., modulo=..., entidad_id=..., datos_anteriores=..., datos_nuevos=...)`
  **antes** del `db.commit()`. Usar `model_to_dict(instance)` para serializar el estado.
  Módulos en MAYÚSCULAS (`MAESTROS_CLIENTES`, `MOVIMIENTOS_OT`, `SEGURIDAD_USUARIOS`, …).
- **POST-redirect-GET:** las mutaciones de UI devuelven `RedirectResponse(url, status_code=303)`, no HTML directo.
- **Claves naturales normalizadas:** `rut`, `patente`, `codigo` se guardan con `.strip().upper()`. Replicar al crear/editar/buscar.
- **Errores de integridad:** envolver `db.commit()` en `try/except IntegrityError` → `rollback()` + `HTTPException(400, detail=...)` con mensaje en español.
- **Enums** centralizados en `app/models/enums.py` (`StrEnum`). Reusar, no redefinir strings.
- **Cálculos de negocio:** los totales de mano de obra/IVA 19% viven en `app/services/costos_service.py` (`calcular_totales_mano_obra`, con tests en `tests/test_costos.py`). Nuevos cálculos de negocio van a un service, no inline en el router.
- **HTMX:** patrones en `PromptModelo §8` (hx-get a modal, hx-post actualiza tabla, hx-delete con confirmación). Sin JavaScript a mano.

### Autenticación web (sesión por cookie)

- Las páginas server-side se protegen con la cookie **`session_token`** (HttpOnly), no con
  el header Bearer (eso es solo para la API JSON `/auth/*`). Modelo en `app/core/web_auth.py`.
- Routers protegidos vía `dependencies=[Depends(require_user)]` a **nivel de APIRouter**
  (`web`, `maestros`, `movimientos`, `seguridad`). Para proteger un router nuevo, agregá esa
  dependency al constructor — no hace falta tocar cada ruta. Públicos: `/login`, `/auth/*`,
  `/system/*`, `/api`, `/static`.
- `require_user` exige sesión **y** `debe_cambiar_password=False`; si está pendiente, el
  handler redirige a `/cambiar-password`. Para rutas que deben verse con el cambio pendiente,
  usar `require_user_pwchange_ok`.
- No-autenticado → `/login`; en peticiones HTMX se responde `HX-Redirect` (ver handlers en `app/main.py`).
- El usuario logueado queda en `request.state.user` (lo usa la navbar). Login/logout/cambio
  en `app/routes/web_auth.py`; templates standalone `pages/login.html` y `pages/cambiar_password.html`.
- En **tests**, autenticar al `TestClient` con `POST /login` (form). Requiere `COOKIE_SECURE=False` (default en dev).

## 7. Cosas que NO hacer / cuidado

- **No** tocar `requirements.txt` (fijar/quitar libs) sin OK explícito del usuario.
- **No** commitear `.env` (está gitignoreado). Los secretos van solo ahí.
- **No** asumir que la app es stateless: el logout invalida la sesión en DB; un JWT válido con sesión inactiva/expirada se rechaza.
- **Seguridad (estado al 2026-06-15):** CORS por orígenes explícitos (`CORS_ORIGINS`), `SECRET_KEY` validado contra placeholders, y páginas web protegidas por sesión (ver arriba) — los tres hallazgos P1 del `AUDIT_REPORT.md` están resueltos. Para **producción** falta: `COOKIE_SECURE=True` (HTTPS) y restringir `CORS_ORIGINS` al dominio real. No reintroducir `allow_origins=["*"]` ni dejar rutas nuevas sin guard.

## 8. MCP

La config MCP del proyecto vive en `.mcp.json` (raíz) — un servidor PostgreSQL apuntando
a `${DATABASE_URL}`. Requiere Node/`npx`. Si no usás MCP, podés ignorarlo; no es necesario
para correr la app ni los tests.

## 9. Repositorio remoto y despliegue

### 9.1 Sincronización con remoto (obligatorio)

Las publicaciones del repositorio local **deben sincronizarse con un remoto en GitHub y/o
GitLab**. Al publicar: configurar el/los remoto(s) (`git remote add ...`) y hacer `git push`
de la rama `main`. Una vez que se decide publicar, el repo no debe quedar solo en disco.

### 9.2 Despliegue en el servidor vía SSH (a definir al publicar)

El repositorio **debe sincronizarse con el servidor de despliegue mediante técnicas de
despliegue por SSH**.

> **Por ahora esto queda solo enunciado.** Cuando se suba/publique el repositorio, si la
> configuración de despliegue **no está definida**, se debe agregar en ese momento **todo lo
> necesario** para el despliegue. Parámetros a completar (TBD):
>
> - Clave SSH (par pública/privada) — TBD
> - IP del servidor — TBD
> - Host / hostname — TBD
> - Usuario de despliegue — TBD
> - Ruta de destino en el servidor — TBD
> - Método de sincronización (p. ej. `git pull` en el server, `rsync`, o hook de deploy) — TBD

### 9.3 Requisitos del servidor de despliegue (obligatorio)

El servidor de despliegue **debe contar con PostgreSQL** y con **todo lo necesario para el
correcto funcionamiento del sistema**:

- **PostgreSQL** instalado y accesible (base creada según `.env`).
- **Python 3.11+** con un entorno virtual y las dependencias de `requirements.txt`.
- **Variables de entorno** (`.env`) configuradas para el server, con `SECRET_KEY` fuerte,
  `COOKIE_SECURE=True` (si hay HTTPS) y `CORS_ORIGINS` del dominio real.
- **Esquema migrado** (`alembic upgrade head`) y **datos base sembrados** (`python -m database.seed`).
