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

- [ ] **Tests:** ampliar `tests/test_smoke.py` (hoy 5 tests, incluido guard de sesión y gate
      de cambio de password). Falta cubrir cálculos de mano de obra/IVA, sincronización
      roles↔permisos y expiración de sesión a nivel unitario. — [ID-T04]
- [ ] **Pytest opcional:** la suite es `unittest`. Si se adopta pytest, declararlo en
      `requirements.txt` (hoy `.gitignore` ya ignora `.pytest_cache/` pero pytest no está instalado). — [ID-T04]

## Prioridad 3 — Higiene del repo (requiere OK para tocar requirements.txt)

- [ ] **Reconciliar dependencias:** decidir sobre `aiofiles` y `email-validator` (sin uso
      directo) — usar o remover. Marcar `httpx` como dep de test. — [ID-T06]
- [ ] **Dos venvs:** consolidar a uno. Agregar `.venv/` a `.gitignore` o eliminarlo. — [ID-T05]
- [ ] **Control de versiones:** el proyecto no es un repo git. Evaluar `git init` para
      versionar el harness y habilitar `/code-review`. — [ID-T07]

## Fase 2 — Funcionalidad (de `PromptModelo`)

- [ ] **Reportes:** OT por período / por técnico / por cliente-vehículo. — [ID-T08]
- [ ] Modal HTMX real para altas/edición (hoy varias pantallas usan página de edición dedicada).
- [ ] Cambio de estado de OT vía `hx-patch` sobre el badge (PromptModelo §8).
