@echo off
setlocal
cd /d "%~dp0"

python -m src.contabil_automation.apply_repeated_classification ^
  --repeated "data\output\classificacao_repetidos.csv" ^
  --rules "config\categorias.csv" ^
  --batch "data\output\classificacao_repetidos_aprovadas.csv"

echo.
echo Reprocessando arquivo para Domínio...
call "RODAR_UPLOAD_DOMINIO.bat"
