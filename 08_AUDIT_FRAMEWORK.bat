@echo off
cd /d "%~dp0"
call "%~dp0RUN_PYTHON.bat" audit_framework.py
if errorlevel 1 (echo ERRO: auditoria falhou.) else (echo AUDITORIA CONCLUIDA.)
pause
