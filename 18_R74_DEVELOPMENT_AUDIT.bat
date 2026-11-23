@echo off
setlocal
cd /d "%~dp0"
call "%~dp0RUN_PYTHON.bat" r74_transition_audit.py development
if errorlevel 1 goto :fail
echo Envie results\r74_transition_audit.json e results\r74_transition_trace.csv
pause
exit /b 0
:fail
echo ERRO E3-R74
pause
exit /b 1
