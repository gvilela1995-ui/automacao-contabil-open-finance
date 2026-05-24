@echo off
setlocal
cd /d "%~dp0"

if not exist "data\xml" mkdir "data\xml"

echo Coloque os XMLs em data\xml e pressione uma tecla.
pause

python -m src.contabil_automation.xml_import --xml-dir "data\xml" --output "data\output\xml_resumo.csv"

echo.
echo Resumo gerado em data\output\xml_resumo.csv
echo.
pause
