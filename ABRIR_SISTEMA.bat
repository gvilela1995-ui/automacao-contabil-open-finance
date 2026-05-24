@echo off
setlocal
cd /d "%~dp0"

start "" "http://127.0.0.1:8765"
set APP_HOST=127.0.0.1
set APP_PORT=8765
python -m src.contabil_automation.web_app
