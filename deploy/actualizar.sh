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
sleep 3
systemctl is-active talleres

echo ">> Verificar respuesta local"
curl -s -o /dev/null -w "/login -> HTTP %{http_code}\n" http://127.0.0.1:8002/login
echo ">> Listo."
