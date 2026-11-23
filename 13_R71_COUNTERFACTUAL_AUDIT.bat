@echo off
setlocal
cd /d "%~dp0"
call "%~dp0RUN_PYTHON.bat" r71_counterfactual_audit.py
if errorlevel 1 goto :fail
echo.
echo Envie: results\r71_counterfactual_audit.json
pause
exit /b 0
:fail
echo ERRO: auditoria E3-R71 nao concluida.
pause
exit /b 1
