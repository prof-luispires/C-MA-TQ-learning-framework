@echo off
cd /d "%~dp0"
call "%~dp0RUN_PYTHON.bat" runner.py check
if errorlevel 1 echo ERRO: execucao nao concluida.
pause
