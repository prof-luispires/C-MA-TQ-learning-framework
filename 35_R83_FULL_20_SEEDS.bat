@echo off
cd /d "%~dp0"
set R83_MODE=FULL
call RUN_PYTHON.bat r83_campaign.py
if errorlevel 1 (echo R83 FAIL & exit /b 1)
echo R83 FULL PASS
pause
