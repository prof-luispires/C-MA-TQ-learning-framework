@echo off
cd /d "%~dp0"
call "%~dp0RUN_PYTHON.bat" learning_diagnostic.py
if errorlevel 1 (echo ERRO: diagnostico falhou.) else (echo DIAGNOSTICO CONCLUIDO.)
pause
