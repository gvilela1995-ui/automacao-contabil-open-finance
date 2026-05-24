@echo off
setlocal
cd /d "%~dp0"

echo.
echo ==========================================
echo  Importar Extrato Sem Open Finance
echo ==========================================
echo.
set /p FILE_PATH=Informe o caminho do OFX ou CSV bancario: 
set /p CLIENT_ID=Informe o client_id do cliente: 
set /p ACCOUNT_ID=Informe o account_id da conta (Enter para conta_manual): 
if "%ACCOUNT_ID%"=="" set ACCOUNT_ID=conta_manual

python -m src.contabil_automation.import_bank_file ^
  --file "%FILE_PATH%" ^
  --client-id "%CLIENT_ID%" ^
  --account-id "%ACCOUNT_ID%" ^
  --output "data\input\transacoes_upload.csv"

echo.
echo Agora rode:
echo   ABRIR_CLASSIFICACAO.bat
echo ou:
echo   RODAR_UPLOAD_DOMINIO.bat
echo.
pause
