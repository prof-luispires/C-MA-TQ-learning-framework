@echo off
cd /d "%~dp0"
call RUN_PYTHON.bat r82_freeze_readiness.py
if errorlevel 1 (echo R82 FAIL & exit /b 1)
echo R82 PASS - results\r82_freeze_readiness.json
pause
