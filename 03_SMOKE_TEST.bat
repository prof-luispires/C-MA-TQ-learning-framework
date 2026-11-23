@echo off
cd /d "%~dp0"
call "%~dp0RUN_PYTHON.bat" runner.py smoke
if errorlevel 1 echo ERRO: execucao nao concluida.
pause
