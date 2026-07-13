# NEXT_STEPS.md — TALLERES

> Última actualización: 2026-07-13. Pasos derivados de `AUDIT_REPORT.md` + despliegue.
> El sistema funciona, la suite (19 tests) pasa y **está desplegado en producción**
> (https://taller.flexconsultora.cl). Lo que queda es deuda de fase 2 y mejoras, no bloqueante.
>
> **PRÓXIMO FOCO (acordado):** revisión de la **funcionalidad y la UI** de la app
> (recorrido vs `PromptModelo_TallerMecanico.md`, estado real de pantallas/flujos, UX/HTMX).
> La **paridad visual server = local** ya quedó resuelta (ver "Sesión 2026-07-13").

## Prioridad 1 — Seguridad (antes de cualquier exposición fuera de localhost)

- [x] **CORS:** corregido (2026-06-15). `allow_origins` ahora es `settings.cors_origins_list`
      (lista explícita configurable vía `CORS_ORIGINS` en `.env`). (`app/main.py`, `config/settings.py`) — [ID-T01]
- [x] **SECRET_KEY:** rotado a clave fuerte (86 chars) y `field_validator` que aborta el
      arranque ante placeholder o <32 chars. (`.env`, `config/settings.py`) — [ID-T02]
- [x] **Auth en páginas web:** sesión por cookie (`session_token`) + guard `require_user` a
      nivel de router en `web`/`maestros`/`movimientos`/`seguridad`; no autenticado → `/login`.
      (`app/core/web_auth.py`, `app/routes/web_auth.py`, `app/main.py`) — [ID-T03]
- [x] **Forzar cambio de password:** login de usuario con `debe_cambiar_password` redirige a
      `/cambiar-password` y bloquea el resto hasta cambiarla. — [ID-T03]
- [ ] **Producción:** activar `COOKIE_SECURE=True` (HTTPS) y restringir `CORS_ORIGINS` al dominio real.

## Prioridad 2 — Cobertura y herramientas

- [x] **Tests:** suite de **19 tests** (unittest): smoke de integración + unitarios de
      costos/IVA (`test_costos`) + sincronización roles↔permisos (`test_seguridad_sync`) +
      sesiones (`test_auth_sessions`). — [ID-T04]
- [ ] **Pytest opcional:** la suite es `unittest`. Si se adopta pytest, declararlo en
      `requirements.txt` (hoy `.gitignore` ya ignora `.pytest_cache/` pero pytest no está instalado). — [ID-T04]

## Prioridad 3 — Higiene del repo (requiere OK para tocar requirements.txt)

- [x] **Reconciliar dependencias:** removidos `aiofiles` y `email-validator` (sin uso);
      `httpx` anotado como dep de test. `pip check` limpio, tests 5/5. — [ID-T06]
- [x] **Dos venvs:** eliminado `.venv/` del disco (estaba vacío, Python 3.13.2 sin deps) y
      agregado a `.gitignore`. Queda solo `venv/` (Python 3.11.2). — [ID-T05]
- [x] **Control de versiones:** repo git inicializado (rama `main`, commit inicial `836eac1`),
      con `.env` y venvs excluidos. — [ID-T07]

## Publicación y despliegue (política del harness — `CLAUDE.md §9`)

- [x] **Remoto:** publicado en GitHub → `https://github.com/jesicacv/TALLERES` (rama `main`,
      8 commits). Falta opcionalmente espejarlo en GitLab. — [CLAUDE.md §9.1]
- [x] **Despliegue SSH:** DESPLEGADO el 2026-06-27 en OCI (Oracle Linux 9, server compartido)
      → **https://taller.flexconsultora.cl**. uvicorn `127.0.0.1:8002` + `talleres.service`
      (systemd) + nginx/Certbot (HTTPS). Sync por **`git pull`** (`deploy/actualizar.sh`).
      Datos sensibles en `.env.deploy` (gitignoreado). Runbook en `deploy/README.md`. — [CLAUDE.md §9.2]
- [x] **Servidor de despliegue:** provisionado — PostgreSQL (base/rol `talleres`), Python 3.11.13
      + venv + deps, `.env` del server (`SECRET_KEY` fuerte, `DEBUG=False`, `COOKIE_SECURE=True`,
      `CORS_ORIGINS=https://taller.flexconsultora.cl`), `alembic upgrade head` + seed. — [CLAUDE.md §9.3]
- [x] **Post-despliegue — acceso admin:** resuelto el 2026-07-13. El `admin` de prod tenía un
      hash que no correspondía a ninguna clave conocida (ni la semilla ni la de `.env.deploy`),
      y además `debe_cambiar_password=True` empujaba a la pantalla de cambio forzado. Se reseteó
      la clave a la que ya declaraba `ADMIN_WEB_PASSWORD` en `.env.deploy`, se puso
      `debe_cambiar_password=False` y se invalidaron las sesiones activas viejas. Login verificado
      end-to-end (`POST /login` → 303 + cookie `Secure`; `GET /` → 200). Nota: **no existe bloqueo
      por intentos fallidos** en el código (`IntentoLogin` solo registra).
- [ ] **Post-despliegue (resto):** opcional espejar el repo en GitLab; considerar migrar el PAT de
      GitHub a fine-grained (mín. privilegio).

## Sesión 2026-07-13 — Paridad de UI server = local + acceso admin

- [x] **Fuente oficial Poppins.** No estaba importada en ningún archivo: local se veía bien por
      el default del sistema, no por diseño. Ahora se carga por **Google Fonts** y se fija como
      fuente base en `layout.html`, `login.html` y `cambiar_password.html`, vía
      `tailwind.config.fontFamily.sans` + `<style>` inline, con fallback final `sans-serif`.
      **Deliberadamente NO va en `app.css`**, para que aplique aunque el CSS estático no cargue.
- [x] **`/static` daba 403 en el server** → `app.css` no cargaba → el menú lateral salía corrido
      y sin resaltado. Causa: `/home/opc` es `700` (`drwx------`) y el worker de nginx no puede
      atravesarlo (`open() failed (13: Permission denied)`; SELinux está *Permissive*, no era él).
      **Fix:** se eliminó `location /static/` de `taller.conf` → `/static` cae al `proxy_pass` y
      lo sirve la app FastAPI (corre como `opc`, sí puede leer). Aislado a TALLERES, sin tocar
      permisos del server compartido. Versionado en `deploy/taller.conf.example`. Commit `e896f9b`.
- [ ] **Gotcha abierto (otra app):** VF_PRESUPUESTO sufre el **mismo** 403 (`/static/img/logo.png`).
      No se tocó (regla de despliegue aditivo). Si algún día se quiere arreglar de raíz para todas
      las apps: `chmod 711 /home/opc` — pero es un cambio al server compartido, hay que acordarlo.

## Sesión 2026-07-13 (2) — Tipos de Vehículo oculto + credencial admin desde `.env`

- [x] **"Tipos de Vehículo" eliminado de la UI.** Era una pantalla de **solo lectura** (los "botones"
      eran cards): el tipo es un `StrEnum` de Python + enum nativo de PostgreSQL, no una tabla, así
      que nunca tuvo ABM. Decisión: queda como **catálogo interno**, administrable solo por el
      desarrollador. Se quitó el link del sidebar, la ruta `GET /maestros/tipos-vehiculo` y el
      template `maestros_tipos_vehiculo.html`. El enum sigue alimentando el `<select>` de vehículos.
      **Agregar un tipo requiere DOS pasos** (documentado en el docstring de `TipoVehiculoEnum`):
      migración `ALTER TYPE tipo_vehiculo_enum ADD VALUE` **y** el miembro en el enum de Python —
      solo por base falla con `LookupError` al leer.
- [x] **Credencial del admin desde `.env`.** `ADMIN_WEB_USER` / `ADMIN_WEB_PASSWORD` pasaron de ser
      solo una anotación en `.env.deploy` a **settings reales** (`config/settings.py`, con default al
      histórico `Admin123!` para no romper el arranque donde no estén definidas). `database/seed.py`
      las usa al crear el admin, y `debe_cambiar_password` ahora es `True` **solo** si quedó la clave
      débil por defecto. Documentadas en `.env.example` (junto con `COOKIE_SECURE`).
- [ ] **Ojo — sin base de test dedicada:** los tests corren contra la **DB de `.env`** (la de dev).
      `test_smoke.test_auth_flow_writes_audit_events` se loguea con el admin real usando la clave de
      `.env`, así que **si la clave del admin en la base deja de coincidir con `ADMIN_WEB_PASSWORD`,
      ese test falla con 401** (fue justamente lo que pasó tras el reseteo manual del 2026-07-13).
      Opción pendiente si molesta: desacoplar el test a su propio usuario, o crear una DB de test.
- [x] **Server:** `ADMIN_WEB_USER` / `ADMIN_WEB_PASSWORD` agregadas al `.env` de producción
      (backup previo `.env.bak-*`, permisos `600`). **Desplegado** (commits `d591b40` + `a336fdd`)
      y verificado en https://taller.flexconsultora.cl: `/login` 200, login admin 303 + dashboard 200,
      `/maestros/tipos-vehiculo` → **404**, sidebar sin el link, y el `<select>` de tipos sigue vivo
      en el alta de vehículos.
- [x] **`deploy/actualizar.sh`:** el `sleep 3` fijo tras el restart era más corto que el arranque de
      uvicorn (~5 s), y la verificación final daba un falso `HTTP 000` con el servicio sano. Ahora
      reintenta hasta 15 s y, si falla, imprime los logs del servicio. Commit `a336fdd`.

## Fase 2 — Funcionalidad (de `PromptModelo`)

- [ ] **Reportes:** OT por período / por técnico / por cliente-vehículo. — [ID-T08]
- [ ] Modal HTMX real para altas/edición (hoy varias pantallas usan página de edición dedicada).
- [ ] Cambio de estado de OT vía `hx-patch` sobre el badge (PromptModelo §8).

## Prompt de continuidad (para retomar en otra sesión)

> Proyecto **TALLERES** (gestión de taller mecánico, FastAPI + HTMX/Tailwind +
> PostgreSQL/SQLAlchemy). Harness Flex aplicado (T01–T07 cerrados), publicado en
> **https://github.com/jesicacv/TALLERES** (repo **público**, rama `main`) y **desplegado en
> producción** en **https://taller.flexconsultora.cl** (desde 2026-06-27). Suite: **19/19 OK**.
>
> **Despliegue (OCI, Oracle Linux 9, server COMPARTIDO de Flex — no pisar presupuesto/fn/n8n):**
> app en `/home/opc/proyectos_python/TALLERES`, uvicorn `127.0.0.1:8002` vía `talleres.service`
> (systemd, `enabled`), nginx `conf.d/taller.conf` + Certbot (HTTPS). DB/rol `talleres` en
> PostgreSQL local. Redespliegue: `bash deploy/actualizar.sh` en el server (hace `git pull` +
> deps + `alembic upgrade head` + restart + verifica `/login`). Datos SSH sensibles en
> `.env.deploy` (gitignoreado); clave privada en `C:\llave_osi\ssh-key-2025-11-18.key`.
> **Ojo al operar por SSH desde Windows:** Python en modo texto traduce `
` a `
` y el bash
> remoto muere con `$'': command not found` — mandar el script como **bytes**.
>
> **Último trabajo (sesión 2026-07-13 (2), commits `d591b40` y `a336fdd`, desplegados y verificados):**
> 1. **"Tipos de Vehículo" eliminado de la UI.** El usuario notó que "solo se ven botones" y no podía
>    dar de alta: era una pantalla de **solo lectura** (los "botones" eran cards) porque el tipo es un
>    `StrEnum` de Python + enum nativo de PostgreSQL, **no una tabla** — nunca tuvo ABM, y así lo define
>    la spec. **Decisión del usuario:** queda como catálogo interno, se agrega por base/código si hace
>    falta, y la opción se oculta. Se quitaron el link del sidebar, la ruta `GET /maestros/tipos-vehiculo`
>    (hoy **404**) y el template. El enum sigue alimentando el `<select>` de vehículos. **Agregar un tipo
>    exige DOS pasos** (documentado en el docstring de `TipoVehiculoEnum`): migración `ALTER TYPE
>    tipo_vehiculo_enum ADD VALUE` **y** el miembro en el enum de Python; solo por base falla con
>    `LookupError` al leer.
> 2. **Credencial admin desde `.env`.** `ADMIN_WEB_USER`/`ADMIN_WEB_PASSWORD` eran solo una anotación en
>    `.env.deploy` — **ningún código las leía**. Ahora son settings reales (`config/settings.py`) que usa
>    `database/seed.py`, **con default** al histórico `Admin123!` (obligatorias romperían el arranque donde
>    no estén definidas). `debe_cambiar_password` se fuerza **solo** si quedó la clave débil por defecto.
>    Ya están en el `.env` local y en el del **server**. El seed sigue siendo idempotente: **no pisa la
>    clave de un admin existente**.
> 3. **`deploy/actualizar.sh`:** el `sleep 3` era más corto que el arranque de uvicorn (~5 s) → falso
>    `HTTP 000`. Ahora reintenta hasta 15 s y vuelca logs si falla.
>
> **Dónde retomar (foco acordado):** sigue la **revisión de funcionalidad y UI**, conducida por el
> usuario: él recorre la app y consulta puntualmente. Método acordado: *"yo reviso y te voy a preguntar
> según necesidad"* — **no** arrancar un inventario o recorrido completo sin que lo pida.
>
> **Deuda conocida:** (a) **No hay base de test dedicada** — los tests corren contra la DB de `.env` (la
> de dev), y `test_smoke.test_auth_flow_writes_audit_events` se loguea con el admin real usando
> `ADMIN_WEB_PASSWORD`: si la clave del admin en la base deja de coincidir con `.env`, ese test falla con
> **401** (fue exactamente el síntoma de esta sesión). El usuario prefirió esto antes que desacoplar el
> test a su propio usuario. (b) [ID-T08] Reportes fase 2 (usar `costos_service.py`; `ot_repuestos` no tiene
> total precalculado). (c) Modal HTMX real para altas/edición; cambio de estado de OT vía `hx-patch`.
> (d) VF_PRESUPUESTO arrastra el mismo **403 de `/static`** (no se tocó: despliegue aditivo). (e) Opcional:
> espejar repo en GitLab; migrar PAT de GitHub a fine-grained. (f) **No hay bloqueo por intentos fallidos
> de login** (`IntentoLogin` solo registra).
>
> Credencial admin (prod y local, la misma): usuario `admin`, clave en `ADMIN_WEB_PASSWORD` del `.env`.
> **Todo el contenido va en español** (CLAUDE.md §0); ante dudas, **consultar y ofrecer opciones** (§0.1).
