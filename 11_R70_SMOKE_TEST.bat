@echo off
cd /d "%~dp0"
call "%~dp0RUN_PYTHON.bat" runner.py r70_smoke
if errorlevel 1 goto :fail
call "%~dp0RUN_PYTHON.bat" r70_learning_audit.py
if errorlevel 1 goto :fail
echo Enviar results\r70_learning_audit.json
pause
exit /b 0
:fail
echo ERRO NO TESTE R70
pause
exit /b 1
