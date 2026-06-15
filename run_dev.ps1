<#
    run_dev.ps1 — Lanzador de desarrollo (equivalente PowerShell de lanzar_app.bat)
    App de Gestion de Taller Mecanico — Flex Consultora
    Levanta uvicorn con recarga en caliente en http://127.0.0.1:8000
#>

$ErrorActionPreference = 'Stop'
Set-Location -Path $PSScriptRoot

$python = Join-Path $PSScriptRoot 'venv\Scripts\python.exe'

if (-not (Test-Path $python)) {
    Write-Host '[ERROR] No se encontro el interprete en venv\Scripts\python.exe' -ForegroundColor Red
    Write-Host 'Verifica que el entorno virtual del proyecto exista (python -m venv venv).'
    exit 1
}

if (-not (Test-Path (Join-Path $PSScriptRoot '.env'))) {
    Write-Host '[ERROR] No se encontro el archivo .env' -ForegroundColor Red
    Write-Host 'Crea el archivo usando .env.example como base.'
    exit 1
}

Write-Host 'Iniciando Gestion Taller Mecanico...' -ForegroundColor Green
Write-Host 'URL : http://127.0.0.1:8000'
Write-Host 'Docs: http://127.0.0.1:8000/docs'
Write-Host ''

& $python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
