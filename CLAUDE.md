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

## 0.1 Reglas de trabajo del agente (obligatorias)

- **Prompt de continuidad en cada update de NEXT_STEPS:** cada vez que se solicite actualizar
  los próximos pasos (`NEXT_STEPS.md`), el agente **debe** entregar además un **prompt de
  continuidad** (resumen de estado + dónde retomar) para poder reanudar el trabajo en otra sesión.
- **Apegarse a lo indicado, dentro de harness / spec / stack:** seguir siempre lo solicitado y
  mantenerse **dentro de las consideraciones del harness** (este `CLAUDE.md`), la **especificación**
  ([`PromptModelo_TallerMecanico.md`](PromptModelo_TallerMecanico.md)) y el **stack técnico**
  ([`TECH_STACK.md`](TECH_STACK.md)). No introducir tecnologías, patrones ni dependencias fuera de
  eso sin acuerdo previo.
- **Ante dudas, consultar y ofrecer opciones — no afirmar resoluciones:** si hay ambigüedad o más
  de un camino válido, **preguntar** y **presentar opciones** con sus implicancias, en lugar de
  afirmar una resolución como única o ya decidida.

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

**Usuario semilla:** el seed crea el admin con la credencial de `.env`
(`ADMIN_WEB_USER` / `ADMIN_WEB_PASSWORD`). Si esas variables no están definidas, cae al default
histórico `admin` / `Admin123!` **y** marca `debe_cambiar_password=True` (para forzar salir de la
clave débil conocida); si la clave viene del `.env`, no fuerza el cambio. El seed es idempotente:
**no pisa la clave de un admin que ya existe** en la base — para rotarla hay que hacerlo a mano.

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

La config MCP del proyecto vive en `.mcp.json` (raíz). Servidores:

- **`postgres_taller`** — PostgreSQL apuntando a `${DATABASE_URL}`. Requiere Node/`npx`.
- **`github`** — servidor remoto oficial de GitHub (`https://api.githubcopilot.com/mcp/`),
  autenticado con `Authorization: Bearer ${GITHUB_PERSONAL_ACCESS_TOKEN}`. No requiere Docker
  ni instalación local. Habilita las operaciones de GitHub del harness ([§9.1](#91-sincronización-con-remoto-obligatorio)).

**Setup del MCP de GitHub:**

1. Crear un **Personal Access Token** en GitHub (fine-grained o classic con scope `repo`).
2. Exponerlo como **variable de entorno** antes de lanzar el agente (el `${...}` de `.mcp.json`
   se expande desde el entorno del proceso, **no** desde `.env`):
   ```powershell
   setx GITHUB_PERSONAL_ACCESS_TOKEN "ghp_xxx"   # persistente (reabrir terminal)
   # o por sesión:  $env:GITHUB_PERSONAL_ACCESS_TOKEN = "ghp_xxx"
   ```
3. El token **nunca** se hardcodea en `.mcp.json` (que está versionado) ni se commitea.

> Alternativa sin remoto (si se prefiere local): servidor oficial vía Docker
> `ghcr.io/github/github-mcp-server` con `GITHUB_PERSONAL_ACCESS_TOKEN`. Requiere Docker.

Si no usás MCP, podés ignorarlo; no es necesario para correr la app ni los tests.

## 9. Repositorio remoto y despliegue

### 9.1 Sincronización con remoto (obligatorio)

Las publicaciones del repositorio local **deben sincronizarse con un remoto en GitHub y/o
GitLab**. Al publicar: configurar el/los remoto(s) (`git remote add ...`) y hacer `git push`
de la rama `main`. Una vez que se decide publicar, el repo no debe quedar solo en disco.

### 9.2 Despliegue en el servidor vía SSH (DESPLEGADO)

El repositorio se sincroniza con el servidor de despliegue mediante **SSH**. **Desplegado
el 2026-06-27** en producción: **https://taller.flexconsultora.cl**.

- **Servidor:** OCI / Oracle Linux 9, **compartido** con otras apps de Flex (presupuesto,
  fuerzanatural, n8n). El despliegue de TALLERES es **aditivo**: no toca las demás apps.
- **App:** uvicorn en `127.0.0.1:8002` (servicio `talleres.service`, systemd `enabled`),
  detrás de nginx + Certbot (HTTPS, redirect 80→443).
- **Método de sync:** **`git pull`** en el servidor (repo público). Redespliegue con
  `deploy/actualizar.sh`.
- **Runbook completo y artefactos versionados:** [`deploy/README.md`](deploy/README.md),
  [`deploy/talleres.service`](deploy/talleres.service), [`deploy/taller.conf.example`](deploy/taller.conf.example).
- **Parámetros sensibles** (IP, usuario SSH, ruta de la clave privada) **NO se versionan**:
  viven en `.env.deploy` (gitignoreado) en la máquina del operador. El repo es **público**.

> Para un despliegue nuevo en otro server, completar esos parámetros en `.env.deploy` y
> seguir la provisión one-time del runbook. Antes de emitir el certificado, debe existir el
> registro **DNS A** del subdominio → IP del servidor (acción del dueño del dominio).

### 9.3 Requisitos del servidor de despliegue (obligatorio) — CUMPLIDO

El servidor de despliegue **debe contar con PostgreSQL** y con **todo lo necesario para el
correcto funcionamiento del sistema** (estado actual en `taller.flexconsultora.cl`):

- **PostgreSQL** instalado y accesible — base y rol `talleres` creados (local `:5432`). ✓
- **Python 3.11+** con venv y las dependencias de `requirements.txt` — instalado 3.11.13. ✓
- **Variables de entorno** (`.env`) del server con `SECRET_KEY` fuerte, `DEBUG=False`,
  `COOKIE_SECURE=True` y `CORS_ORIGINS=https://taller.flexconsultora.cl`. ✓
- **Esquema migrado** (`alembic upgrade head`) y **datos base sembrados** (`python -m database.seed`). ✓
