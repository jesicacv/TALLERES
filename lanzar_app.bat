@echo off
setlocal

cd /d "%~dp0"

if not exist "venv\Scripts\python.exe" (
    echo [ERROR] No se encontro el interprete en venv\Scripts\python.exe
    echo Verifica que el entorno virtual del proyecto exista.
    pause
    exit /b 1
)

if not exist ".env" (
    echo [ERROR] No se encontro el archivo .env
    echo Crea el archivo usando .env.example como base.
    pause
    exit /b 1
)

echo Iniciando Gestion Taller Mecanico...
echo URL: http://127.0.0.1:8000
echo Docs: http://127.0.0.1:8000/docs
echo.

"venv\Scripts\python.exe" -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

if errorlevel 1 (
    echo.
    echo La aplicacion se cerro con error.
    pause
)