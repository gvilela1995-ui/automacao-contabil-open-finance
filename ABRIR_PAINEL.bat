@echo off
setlocal
cd /d "%~dp0"

if not exist "data\output\dashboard.html" (
  echo Painel ainda nao foi gerado. Rodando pipeline primeiro...
  call "RODAR_PIPELINE.bat"
)

start "" "data\output\dashboard.html"
