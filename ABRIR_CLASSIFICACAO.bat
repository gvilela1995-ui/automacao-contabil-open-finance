@echo off
setlocal
cd /d "%~dp0"

python -m src.contabil_automation.classification_review ^
  --input "data\input\transacoes_upload.csv" ^
  --rules "config\categorias.csv" ^
  --output-csv "data\output\classificacao_repetidos.csv" ^
  --output-html "data\output\classificacao_repetidos.html"

start "" "data\output\classificacao_repetidos.html"
start "" "data\output\classificacao_repetidos.csv"

echo.
echo Ajuste o CSV e depois rode APLICAR_CLASSIFICACAO_REPETIDOS.bat
echo.
pause
