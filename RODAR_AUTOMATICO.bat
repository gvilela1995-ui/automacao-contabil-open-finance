@echo off
setlocal
cd /d "%~dp0"

echo.
echo ==========================================
echo  Execucao Automatica Contabil
echo ==========================================
echo.

python -m src.contabil_automation.automatic_runner --config "config\automacao.json"

echo.
echo Saidas:
echo - data\output\dashboard.html
echo - data\output\documentos_prontos
echo - data\output\pendencias
echo - logs
echo.
pause
