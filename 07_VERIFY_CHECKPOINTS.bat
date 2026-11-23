@echo off
cd /d "%~dp0"
call "%~dp0RUN_PYTHON.bat" verify_checkpoints.py
if errorlevel 1 (echo ERRO: verificacao de checkpoints falhou.) else (echo VERIFICACAO CONCLUIDA.)
pause
