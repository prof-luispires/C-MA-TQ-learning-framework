@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
 echo ERRO: Ambiente virtual nao preparado. Execute primeiro 00_INSTALL_ALL.bat
 exit /b 1
)
"%~dp0.venv\Scripts\python.exe" %*
exit /b %errorlevel%
