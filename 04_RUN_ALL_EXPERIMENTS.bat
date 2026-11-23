@echo off
cd /d "%~dp0"
echo AVISO: dados ja examinados - resultados exploratorios, nao confirmatorios.
call "%~dp0RUN_PYTHON.bat" runner.py development --seeds 5 --steps 3500
if errorlevel 1 echo ERRO: execucao nao concluida.
pause
