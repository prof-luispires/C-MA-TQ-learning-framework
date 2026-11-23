@echo off
setlocal
cd /d "%~dp0"
call "%~dp0RUN_PYTHON.bat" r73_stability.py smoke
if errorlevel 1 goto :fail
echo Envie results\r73_stability_audit.json
pause
exit /b 0
:fail
echo ERRO E3-R73
pause
exit /b 1
