#!/usr/bin/env bash
# actualizar.sh — Redespliegue de TALLERES en el servidor (metodo: git pull).
# Ejecutar EN el servidor, como el usuario `opc`, dentro del directorio de la app:
#   cd /home/opc/proyectos_python/TALLERES && bash deploy/actualizar.sh
#
# Trae los ultimos cambios de `main`, actualiza dependencias, aplica migraciones
# y reinicia el servicio systemd. No toca el .env (secretos del servidor).
set -euo pipefail

APP_DIR="/home/opc/proyectos_python/TALLERES"
cd "$APP_DIR"

echo ">> git pull (rama main)"
git pull --ff-only origin main

echo ">> Dependencias"
./venv/bin/python -m pip install -r requirements.txt

echo ">> Migraciones (alembic upgrade head)"
./venv/bin/python -m alembic upgrade head

echo ">> Reiniciar servicio"
sudo systemctl restart talleres
systemctl is-active talleres

echo ">> Verificar respuesta local"
# Los workers de uvicorn tardan unos segundos en aceptar conexiones: reintentamos en vez
# de asumir un sleep fijo (con `sleep 3` daba un falso HTTP 000).
for intento in $(seq 1 15); do
    codigo=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8002/login || true)
    if [ "$codigo" = "200" ]; then
        echo "/login -> HTTP 200 (tras ${intento}s)"
        echo ">> Listo."
        exit 0
    fi
    sleep 1
done

echo "ERROR: /login no respondio 200 tras 15s (ultimo codigo: ${codigo:-000})"
sudo journalctl -u talleres -n 30 --no-pager
exit 1
