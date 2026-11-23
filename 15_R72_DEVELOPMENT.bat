@echo off
setlocal
cd /d "%~dp0"
call "%~dp0RUN_PYTHON.bat" r72_experiment.py development
if errorlevel 1 goto :fail
echo Envie results\r72_structural_audit.json
pause
exit /b 0
:fail
echo ERRO E3-R72
pause
exit /b 1
