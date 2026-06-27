# NEXT_STEPS.md — TALLERES

> Última actualización: 2026-06-27. Pasos derivados de `AUDIT_REPORT.md` + despliegue.
> El sistema funciona, la suite (19 tests) pasa y **está desplegado en producción**
> (https://taller.flexconsultora.cl). Lo que queda es deuda de fase 2 y mejoras, no bloqueante.
>
> **PRÓXIMO FOCO (acordado):** revisión de la **funcionalidad y la UI** de la app
> (recorrido vs `PromptModelo_TallerMecanico.md`, estado real de pantallas/flujos, UX/HTMX).

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
- [ ] **Post-despliegue:** cambiar el password del `admin` semilla en el primer login; opcional
      espejar el repo en GitLab; considerar migrar el PAT de GitHub a fine-grained (mín. privilegio).

## Fase 2 — Funcionalidad (de `PromptModelo`)

- [ ] **Reportes:** OT por período / por técnico / por cliente-vehículo. — [ID-T08]
- [ ] Modal HTMX real para altas/edición (hoy varias pantallas usan página de edición dedicada).
- [ ] Cambio de estado de OT vía `hx-patch` sobre el badge (PromptModelo §8).

## Prompt de continuidad (para retomar en otra sesión)

> Proyecto **TALLERES** (gestión de taller mecánico, FastAPI + HTMX/Tailwind +
> PostgreSQL/SQLAlchemy). Harness Flex aplicado (T01–T07 cerrados), publicado en
> **https://github.com/jesicacv/TALLERES** (repo **público**, rama `main`) y **desplegado
> en producción** el 2026-06-27 en **https://taller.flexconsultora.cl**.
>
> **Despliegue (OCI, Oracle Linux 9, server COMPARTIDO de Flex — no pisar presupuesto/fn/n8n):**
> app en `/home/opc/proyectos_python/TALLERES`, uvicorn `127.0.0.1:8002` vía `talleres.service`
> (systemd, `enabled`), nginx `conf.d/taller.conf` + Certbot (HTTPS, renovación automática).
> DB/rol `talleres` en PostgreSQL local. `.env` del server con `DEBUG=False`,
> `COOKIE_SECURE=True`, `CORS_ORIGINS=https://taller.flexconsultora.cl`. Redespliegue:
> `git pull` → `deploy/actualizar.sh`. Datos SSH sensibles en `.env.deploy` (gitignoreado);
> clave privada en `C:\llave_osi\ssh-key-2025-11-18.key` (fuera del repo). MCP `github`
> conectado (PAT classic scope `repo` en env var `GITHUB_PERSONAL_ACCESS_TOKEN`).
>
> **Dónde retomar (foco acordado):** **revisión de la funcionalidad y la UI de la app.**
> Es decir: recorrer el sistema vs `PromptModelo_TallerMecanico.md`, relevar el estado real de
> pantallas y flujos (clientes/vehículos, OT, mano de obra/repuestos, checklist, técnicos,
> seguridad), y la UX/HTMX (modales, cambios de estado de OT, validaciones). Puede hacerse con
> recorrido en vivo (`run_dev.ps1` o directo sobre https://taller.flexconsultora.cl), inventario
> funcional, o code review de `app/routes` + `app/templates`. Acordar con el usuario el método.
>
> Credencial admin de prod: usuario `admin`, clave en `ADMIN_WEB_PASSWORD` de `.env.deploy`.
>
> **Pendientes secundarios:** [ID-T08] Reportes fase 2 (OT por período/técnico/cliente —
> `ot_repuestos` no tiene total precalculado, usar `costos_service.py`); modal HTMX real para
> altas/edición; cambio de estado de OT vía `hx-patch`; opcional: espejar repo en GitLab,
> migrar PAT de GitHub a fine-grained. **Todo el contenido va en español** (CLAUDE.md §0); ante
> dudas, consultar y ofrecer opciones (§0.1).
