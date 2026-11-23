@echo off
setlocal
cd /d "%~dp0"
if "%~1"=="" (
 echo Utilizacao: 06_ZERO_SHOT_EXTERNAL.bat "C:\dados\ataques_mapeados.csv" "models\central_seed42.pkl"
 echo Requer CSV mapeado, rótulos auditados e checkpoint existente.
 pause
 exit /b 2
)
if "%~2"=="" (
 echo ERRO: indique o checkpoint como segundo argumento.
 pause
 exit /b 2
)
if not exist "results\external" mkdir "results\external"
call "%~dp0RUN_PYTHON.bat" external_zero_shot.py --csv "%~1" --model "%~2" --output "results\external\predictions.csv"
if errorlevel 1 echo ERRO na avaliacao externa. Nao altere os rótulos para forcar compatibilidade.
pause
