@echo off
setlocal
cd /d "%~dp0"

echo.
echo ==========================================
echo  Automacao Contabil Open Finance
echo ==========================================
echo.

where python >nul 2>nul
if errorlevel 1 (
  echo Python nao encontrado no PATH.
  pause
  exit /b 1
)

python -m src.contabil_automation.pipeline ^
  --input "data\input\transacoes_exemplo.csv" ^
  --clients "data\input\clientes.csv" ^
  --rules "config\categorias.csv" ^
  --domain-layout "config\dominio_layout.json" ^
  --conciliation "data\input\conciliacao_exemplo.csv" ^
  --schedules "config\agendamentos.csv" ^
  --stages "config\etapas.csv" ^
  --times "data\input\tempos_cliente.csv" ^
  --errors "data\input\erros_coleta.csv" ^
  --receipts-dir "data\comprovantes" ^
  --output-dir "data\output"

echo.
echo Finalizado. Confira:
echo - data\output\dashboard.html
echo - data\output\documentos_prontos
echo - data\output\pendencias
echo.
pause
