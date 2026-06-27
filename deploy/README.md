# Despliegue — TALLERES

Despliegue en el **servidor compartido de Flex Consultora** (Oracle Cloud Infrastructure,
Oracle Linux 9). El servidor ya corre nginx + Certbot como reverse proxy de varias apps;
TALLERES se suma de forma **aditiva** sin tocar las demás.

> Datos sensibles (IP, usuario SSH, ruta de la clave) **no** se versionan: viven en
> `.env.deploy` (gitignoreado) en la máquina del operador. El repo es público.

## Estado actual

- **URL:** https://taller.flexconsultora.cl  (HTTPS, Let's Encrypt, redirect 80→443)
- **App:** FastAPI/uvicorn en `127.0.0.1:8002` (2 workers), `WorkingDirectory`
  `/home/opc/proyectos_python/TALLERES`, gestionada por `talleres.service` (systemd, `enabled`).
- **DB:** PostgreSQL local `127.0.0.1:5432`, base y rol `talleres` (owner). Esquema por
  Alembic + datos base por `database.seed`.
- **nginx:** `/etc/nginx/conf.d/taller.conf` (bloque 443 gestionado por Certbot).

## Convención del servidor

Cada app vive en `/home/opc/proyectos_python/<APP>` con su `venv`, corre como `opc` en un
puerto local (8000=presupuesto, 8001=flexweb, 8002=taller, 5678=n8n), tras un servicio
`systemd <app>.service` y un `conf.d/<app>.conf` de nginx con subdominio + HTTPS Certbot.

## Provisión inicial (one-time)

Requiere `sudo` (no interactivo en este server) y un registro **DNS A**
`taller.flexconsultora.cl → IP` ya resolviendo.

1. **Python 3.11** (el sistema trae 3.9): `sudo dnf install -y python3.11 python3.11-pip`
2. **Clonar:** `git clone https://github.com/jesicacv/TALLERES.git /home/opc/proyectos_python/TALLERES`
3. **venv + deps:** `python3.11 -m venv venv && ./venv/bin/python -m pip install -r requirements.txt`
4. **DB + rol** (PostgreSQL): crear rol `talleres` con password fuerte y base `talleres OWNER talleres`.
5. **`.env`** en el `WorkingDirectory` (chmod 600), con `DATABASE_URL` a la base `talleres`,
   `SECRET_KEY` fuerte (≥32 chars), `DEBUG=False`, `COOKIE_SECURE=True`,
   `CORS_ORIGINS=https://taller.flexconsultora.cl`.
6. **Esquema + seed:** `./venv/bin/python -m alembic upgrade head` y `./venv/bin/python -m database.seed`.
7. **Servicio:** `sudo cp deploy/talleres.service /etc/systemd/system/ && sudo systemctl daemon-reload && sudo systemctl enable --now talleres`
8. **nginx + HTTPS:** `sudo cp deploy/taller.conf.example /etc/nginx/conf.d/taller.conf`,
   `sudo nginx -t && sudo systemctl reload nginx`, luego
   `sudo /usr/local/bin/certbot --nginx -d taller.flexconsultora.cl --agree-tos --redirect`.

> El **usuario semilla** (`admin / Admin123!`) arranca con `debe_cambiar_password=True`:
> cambiar la contraseña en el primer login.

## Redespliegue (cambios posteriores)

Método de sincronización: **`git pull`** en el servidor.

```bash
cd /home/opc/proyectos_python/TALLERES
bash deploy/actualizar.sh   # git pull + deps + alembic + restart + verificación
```

## Operación

```bash
systemctl status talleres
journalctl -u talleres -f          # logs en vivo
sudo systemctl restart talleres    # reinicio manual
```

El certificado renueva solo (`certbot-renew.timer`).
