# NEXT_STEPS.md — TALLERES

> Última actualización: 2026-06-15. Pasos derivados de `AUDIT_REPORT.md`.
> El sistema funciona y los 3 smoke tests pasan; esto es deuda de robustez/seguridad y
> de funcionalidad de fase 2, no corrección bloqueante.

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

- [ ] **Remoto:** publicar el repo local en GitHub y/o GitLab (`git remote add` + `git push`
      de `main`). Requiere `gh`/credenciales o un remoto creado. — [CLAUDE.md §9.1]
- [ ] **Despliegue SSH (definir al publicar):** al subir el repo, si el despliegue no está
      definido, agregar **todo lo necesario**: clave SSH, IP del servidor, host, usuario,
      ruta de destino y método de sync (`git pull`/`rsync`/hook). — [CLAUDE.md §9.2]
- [ ] **Servidor de despliegue:** provisionar **PostgreSQL** + Python 3.11+ con venv y deps,
      `.env` del server (con `SECRET_KEY` fuerte, `COOKIE_SECURE=True`, `CORS_ORIGINS` real),
      `alembic upgrade head` y `python -m database.seed`. — [CLAUDE.md §9.3]

## Fase 2 — Funcionalidad (de `PromptModelo`)

- [ ] **Reportes:** OT por período / por técnico / por cliente-vehículo. — [ID-T08]
- [ ] Modal HTMX real para altas/edición (hoy varias pantallas usan página de edición dedicada).
- [ ] Cambio de estado de OT vía `hx-patch` sobre el badge (PromptModelo §8).
