@echo off
setlocal
cd /d "%~dp0"

python -m src.contabil_automation.classifiers.batch_import ^
  --batch "data\input\classificacao_lote.csv" ^
  --rules "config\categorias.csv"

echo.
echo Regras atualizadas em config\categorias.csv.
echo Rode RODAR_AUTOMATICO.bat para reprocessar.
echo.
pause
