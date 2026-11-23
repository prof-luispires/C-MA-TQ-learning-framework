@echo off
cd /d "%~dp0"
echo Treino EXPLORATORIO: substitui checkpoints e resultados. NAO executar ainda.
choice /C SN /M "Confirma treino de desenvolvimento R70"
if errorlevel 2 exit /b 0
call "%~dp0RUN_PYTHON.bat" runner.py r70_development --seeds 5 --steps 3500
pause
