@echo off
setlocal
cd /d "%~dp0"

python -m src.contabil_automation.pipeline ^
  --input "data\input\transacoes_upload.csv" ^
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
echo Confira data\output\lancamentos_dominio.txt e data\output\lancamentos_conferencia.xlsx
echo.
pause
