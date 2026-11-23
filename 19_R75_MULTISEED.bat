@echo off
setlocal
cd /d "%~dp0"
call "%~dp0RUN_PYTHON.bat" r75_controlled.py
if errorlevel 1 goto :fail
echo Envie results\r75_structural_audit.json e results\r75_training_td_trace.csv
pause
exit /b 0
:fail
echo ERRO E3-R75
pause
exit /b 1
