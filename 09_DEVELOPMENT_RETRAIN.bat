@echo off
cd /d "%~dp0"
echo ATENCAO: Treino exploratorio, substitui os checkpoints existentes.
choice /C SN /M "Pretende executar o treino exploratorio com 5 sementes"
if errorlevel 2 exit /b 0
call "%~dp0RUN_PYTHON.bat" runner.py development --seeds 5 --steps 3500
if errorlevel 1 (echo ERRO: treino falhou.) else (echo TREINO EXPLORATORIO CONCLUIDO.)
pause
