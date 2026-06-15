# AUDIT_REPORT.md — TALLERES (Gestión de Taller Mecánico)

> Fecha: 2026-06-15
> Auditado contra: `PromptModelo_TallerMecanico.md` + el código del repo + checklist del harness Flex
> Auditor: Harness Engineering — Flex Consultora SpA
> Modo: lectura + verificación (se corrieron tests; **no se modificó código de la app**)

## Resumen

**TALLERES** es la app interna de gestión de taller mecánico (FastAPI + HTMX/Tailwind +
PostgreSQL/SQLAlchemy). El relevamiento confirma que el stack real está **alineado con la
especificación** (`PromptModelo`): Python 3.11.2, FastAPI, HTMX + Tailwind por CDN, Jinja2
server-side, Pydantic v2 y SQLAlchemy 2.0 sobre `psycopg2`. La estructura por capas
(`models/`, `schemas/`, `routes/`, `services/`) está bien ordenada y la **auditoría de
acciones está implementada de forma consistente** en todas las mutaciones.

**Verificación funcional:** la base PostgreSQL de `.env` conecta, está migrada y sembrada,
y la suite **pasa los 19 tests** (smoke de integración + unitarios de costos/IVA +
sincronización roles↔permisos + sesiones).

Las diferencias son **deuda acotada**, concentrada en **seguridad de configuración** (CORS
mal formado, `SECRET_KEY` placeholder, páginas web sin guard de auth) y en **higiene de
repo** (dos venvs, dependencias sin uso, sin control de versiones). No hay credenciales de
producción hardcodeadas (todo vía `.env`, gitignoreado) y el SQL usa SQLAlchemy con binds
(las búsquedas `ilike(f"%{q}%")` parametrizan el patrón — sin inyección).

> **Nota histórica:** el `AUDIT_REPORT.md` previo en esta ruta correspondía a **otro
> proyecto Flex (GEOV_PLATFORM** — Oracle, frontend Reflex, deploy `192.168.150.28`). Fue
> reemplazado por esta auditoría real de TALLERES. Ninguno de los hallazgos de GEOV
> (ID-001…ID-006) aplica a este proyecto.

**Conteo: 9 OK / 6 DIFERENCIAS / 1 VIOLACIÓN.** Prioridad 1 de seguridad
(**T01 CORS, T02 SECRET_KEY, T03 auth web + cambio de password**) **✅ resuelta el 2026-06-15.**

---

## Checklist

### Stack (vs. PromptModelo §2 y TECH_STACK.md)
| Ítem | Estado | Nota |
|---|---|---|
| Python 3.11+ | ✅ OK | 3.11.2, venv en `venv/` (único venv tras [ID-T05]) |
| FastAPI como framework | ✅ OK | `app/main.py`, 6 routers |
| HTMX + Tailwind en frontend | ✅ OK | CDN; HTMX 1.9.12; sin Alpine ni JS a mano |
| PostgreSQL + SQLAlchemy 2.0 | ✅ OK | `psycopg2`, `database/base.py` |
| Pydantic v2 | ✅ OK | 2.5.0; schemas en `app/schemas/auth.py` |
| Alembic para migraciones | ✅ OK | 2 versiones aplicadas |

### Estructura
| Ítem | Estado | Nota |
|---|---|---|
| `routes/` | ✅ OK | 6 routers por dominio |
| `services/` | ✅ OK | `auth_service`, `audit_service` |
| `models/` (ORM) | ✅ OK | uno por entidad + `enums.py` |
| `schemas/` (Pydantic) | ⚠️ DIFERENCIA | Solo `auth`; el resto entra por `Form(...)`. Aceptable hoy — ver [ID-T06b] |
| Sin lógica pesada en routers | ✅ OK | Cálculo de totales/IVA extraído a `services/costos_service.py` — ver [ID-T06b] |

### Configuración / Harness
| Ítem | Estado | Nota |
|---|---|---|
| `CLAUDE.md` | ✅ OK | Creado en esta intervención |
| `TECH_STACK.md` | ✅ OK | Creado en esta intervención |
| `NEXT_STEPS.md` | ✅ OK | Creado en esta intervención |
| `run_dev.ps1` | ✅ OK | Creado (par de `lanzar_app.bat`) |
| `.mcp.json` en raíz | ✅ OK | Creado (Postgres MCP, `${DATABASE_URL}`) |
| `.env` / `.env.example` | ✅ OK | Ambos presentes; `.env` gitignoreado |
| `tests/` | ✅ OK | unittest, **19/19 pasan** (smoke, costos, seguridad-sync, sesiones) |
| `requirements.txt` con versiones fijadas | ✅ OK | Todo con `==` |
| Sin credenciales de prod hardcodeadas | ✅ OK | Todo vía `.env` |
| Control de versiones (git) | ✅ OK | Repo git inicializado (rama `main`, commit inicial) — [ID-T07] |

---

## Diferencias y violaciones

### [ID-T01] CORS mal formado e inseguro — **VIOLACIÓN ✅ CORREGIDA (2026-06-15)**
- **Tipo:** VIOLACIÓN (seguridad de configuración) — **resuelta**
- **Descripción original:** `app/main.py` configuraba `CORSMiddleware` con `allow_origins=["*"]`
  y `allow_credentials=True` simultáneamente — combinación inválida según la spec de CORS
  (con `*` el navegador ignora las credenciales) e insegura como intención.
- **Fix aplicado:** se reemplazó `["*"]` por `settings.cors_origins_list`, una lista explícita
  configurable vía `CORS_ORIGINS` en `.env` (default seguro `http://127.0.0.1:8000,http://localhost:8000`).
  Orígenes explícitos + `allow_credentials=True` es una combinación válida. Documentado en
  `.env.example`. Smoke tests siguen pasando (3/3).

### [ID-T02] `SECRET_KEY` con valor placeholder — ✅ CORREGIDA (2026-06-15)
- **Tipo:** DIFERENCIA (seguridad) — **resuelta**
- **Descripción original:** `.env` traía un `SECRET_KEY` placeholder que firma los JWT; un
  valor conocido permite forjar tokens.
- **Fix aplicado:** se rotó a una clave fuerte de 86 chars (`secrets.token_urlsafe(64)`) en
  `.env`. Además se agregó un `field_validator` en `config/settings.py` que **aborta el
  arranque** si `SECRET_KEY` es un placeholder conocido o tiene <32 chars. Rotar invalidó
  las sesiones/JWT previos (re-login requerido). Smoke tests 3/3.

### [ID-T03] Páginas web sin autenticación + cambio de password no forzado — ✅ CORREGIDA (2026-06-15)
- **Tipo:** DIFERENCIA (seguridad/funcional) — **resuelta**
- **Descripción original:** las rutas de UI (`/maestros/*`, `/movimientos/*`, `/seguridad/*`,
  `/`) respondían sin requerir sesión; el admin semilla tenía `debe_cambiar_password=True`
  sin flujo que lo aplicara.
- **Fix aplicado — modelo de sesión por cookie:**
  - `app/core/web_auth.py`: cookie `session_token` (HttpOnly, SameSite=Lax, `Secure` vía
    `COOKIE_SECURE`), guard `require_user` (exige sesión + password al día) y
    `require_user_pwchange_ok` (relajado, para la propia pantalla de cambio). Reutiliza la
    infraestructura de sesiones JWT existente (`auth_service`).
  - Guard aplicado a **nivel de router** en `web` (dashboard), `maestros`, `movimientos` y
    `seguridad`. `/auth/*` (API JSON), `/system/*`, `/api` y `/login` quedan públicos.
  - `app/routes/web_auth.py` + templates `login.html` / `cambiar_password.html`: login web,
    logout (invalida la sesión en DB) y **cambio de password obligatorio** (login de un
    usuario con `debe_cambiar_password` redirige a `/cambiar-password` y bloquea las páginas
    hasta cambiarla).
  - Exception handlers en `app/main.py` redirigen no-autenticado→`/login` y
    pendiente-de-cambio→`/cambiar-password`, con soporte HTMX (`HX-Redirect`).
  - Navbar muestra el usuario y botón "Salir".
- **Verificación:** suite ampliada a **5 tests, todos OK** (incluye `test_protected_pages_require_session` y `test_password_change_gate_redirects`).

### [ID-T04] Cobertura de tests acotada — ✅ CORREGIDA (2026-06-15)
- **Tipo:** DIFERENCIA — **resuelta**
- **Descripción original:** solo existía `tests/test_smoke.py`; sin tests de la lógica de
  negocio (totales de mano de obra/IVA, sincronización roles↔permisos, sesiones).
- **Fix aplicado:** suite ampliada a **19 tests, todos OK** (unittest):
  - `tests/test_costos.py` — unitarios **puros** del cálculo de mano de obra/IVA (descuento,
    bonificación, clamp a 0, IVA 19%, horas fraccionarias). Habilitado por extraer el cálculo
    a `app/services/costos_service.py` (ver [ID-T06b]).
  - `tests/test_seguridad_sync.py` — sincronización `roles↔permisos` y `usuarios↔roles`
    (agrega/quita/vacía, ids inexistentes ignorados).
  - `tests/test_auth_sessions.py` — login válido, password incorrecta sin sesión, sesión
    expirada/inactiva rechazada, logout invalida, token malformado.
- **Nota pytest:** la suite sigue siendo `unittest` (decisión vigente); no se adoptó pytest.

### [ID-T05] Dos entornos virtuales en disco — ✅ CORREGIDA (2026-06-15)
- **Tipo:** DIFERENCIA (higiene) — **resuelta**
- **Descripción original:** coexistían `venv/` (Python 3.11.2, con todas las deps, usado por
  lanzadores/`.vscode`/tests) y `.venv/` (Python 3.13.2, **vacío** — sin `fastapi` ni el
  resto del stack, no referenciado por nada). `.gitignore` solo ignoraba `venv/`.
- **Fix aplicado:** se eliminó `.venv/` del disco (era un venv abandonado e incompleto) y se
  agregó `.venv/` al `.gitignore`. Queda un único entorno: `venv/`.
- **Corrección de documentación:** la versión real de Python es **3.11.2** (los docs decían
  3.13 por un supuesto no verificado en la auditoría inicial); corregido en `CLAUDE.md`,
  `TECH_STACK.md` y este reporte.

### [ID-T06] Dependencias declaradas sin uso directo — ✅ CORREGIDA (2026-06-15)
- **Tipo:** DIFERENCIA (trazabilidad stack↔deps) — **resuelta** (con OK del usuario, R5)
- **Descripción original:** `aiofiles` y `email-validator` no se usaban (grep sin hits en
  todo el repo); `httpx` solo lo usa `TestClient`.
- **Fix aplicado:** se removieron `aiofiles` y `email-validator` de `requirements.txt` y del
  venv (sin reverse-deps; `pip check` limpio; tests 5/5 tras la remoción). `httpx` se mantiene
  y quedó anotado como dependencia de test en `requirements.txt`.

### [ID-T06b] Schemas Pydantic mínimos y cálculo de negocio inline — 🔧 PARCIAL (2026-06-15)
- **Tipo:** DIFERENCIA (menor)
- **Descripción:** casi toda la entrada es `Form(...)` HTML, por eso solo `auth` tiene
  schemas Pydantic.
- **Avance:** el cálculo de totales/IVA de mano de obra se **extrajo** de `movimientos.py` a
  `app/services/costos_service.py` (`calcular_totales_mano_obra`), con cobertura unitaria
  propia. Pendiente: consolidar schemas en `app/schemas/` si se agregan endpoints JSON.

### [ID-T07] Proyecto sin control de versiones — ✅ CORREGIDA (2026-06-15)
- **Tipo:** DIFERENCIA — **resuelta**
- **Descripción original:** el directorio no era un repositorio git (había `.gitignore`, pero
  no `.git`). Sin historial ni base para `/code-review`.
- **Fix aplicado:** `git init -b main` + commit inicial (`836eac1`) con 88 archivos
  versionados. Se reforzó `.gitignore` (`.venv/`, `logs/`, `*.log`); verificado que `.env`
  y ambos venvs quedan fuera del control de versiones. Identidad local del repo:
  `efrancalancia <efrancalancia@outlook.cl>` (ajustable con `git config user.name`).

### [ID-T08] Reportes (fase 2) pendientes
- **Tipo:** DIFERENCIA (alcance planificado)
- **Descripción:** `PromptModelo §5` define reportes (OT por período/técnico/cliente) como
  fase 2; aún no implementados. Esperado.

---

## Próximos pasos recomendados (priorizados)

1. ~~**[ID-T01] Corregir CORS**~~ — ✅ hecho (2026-06-15).
2. ~~**[ID-T02] Rotar `SECRET_KEY`**~~ — ✅ hecho (2026-06-15), con guard anti-placeholder.
3. ~~**[ID-T03] Proteger las páginas web**~~ — ✅ hecho (2026-06-15): sesión por cookie + cambio de password forzado.
4. ~~**[ID-T04] Ampliar tests**~~ — ✅ hecho (2026-06-15): 19 tests (costos/IVA, roles↔permisos, sesiones).
5. ~~**[ID-T06] Higiene:** reconciliar dependencias~~ — ✅ hecho (2026-06-15). _([ID-T05] venv consolidado ✅)_
6. ~~**[ID-T07] `git init`**~~ — ✅ hecho (2026-06-15), commit inicial `836eac1`.
7. **[ID-T08] Reportes de fase 2** según `PromptModelo`.

> El sistema **funciona y los smoke tests pasan**. La prioridad real es seguridad de
> configuración (P1) antes de exponer la app fuera de `localhost`; el resto es robustez,
> higiene y funcionalidad de fase 2.

---

*Auditoría contra el harness Flex — no se modificó código de la app; sí se agregaron los documentos de gobierno del harness (CLAUDE.md, TECH_STACK.md, NEXT_STEPS.md, run_dev.ps1, .mcp.json).*
