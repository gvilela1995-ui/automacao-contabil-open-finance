@echo off
setlocal
cd /d "%~dp0"

set TASK_NAME=Automacao Contabil Open Finance
set TASK_TIME=07:00

echo Criando tarefa agendada diaria: %TASK_NAME% as %TASK_TIME%
schtasks /Create /TN "%TASK_NAME%" /TR "\"%~dp0RODAR_AUTOMATICO.bat\"" /SC DAILY /ST %TASK_TIME% /F

echo.
echo Tarefa criada. O Windows vai executar o pipeline automaticamente todos os dias.
echo.
pause
