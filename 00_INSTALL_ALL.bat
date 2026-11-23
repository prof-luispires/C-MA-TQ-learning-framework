@echo off
setlocal EnableExtensions
cd /d "%~dp0"
echo ============================================================
echo E3-R65 - Instalacao automatica de dependencias
 echo ============================================================
call "%~dp0FIND_PYTHON.bat"
if errorlevel 1 goto :fail
if exist ".venv\Scripts\python.exe" goto :install
 echo [1/3] A criar ambiente virtual...
"%PYTHON_EXE%" -m venv ".venv"
if errorlevel 1 goto :venv_fail
:install
 echo [2/3] A instalar todas as dependencias (internet necessaria)...
".venv\Scripts\python.exe" -m pip install --disable-pip-version-check -r requirements.txt
if errorlevel 1 goto :fail
 echo [3/3] A verificar dependencias e testes...
".venv\Scripts\python.exe" runner.py check
if errorlevel 1 goto :fail
 echo.
echo INSTALACAO CONCLUIDA. Pode executar 03_SMOKE_TEST.bat
pause
exit /b 0
:venv_fail
echo ERRO: nao foi possivel criar .venv. Verifique se o Python tem o modulo venv.
goto :fail
:fail
echo.
echo INSTALACAO NAO CONCLUIDA. Veja o erro acima.
echo Se nao existir Python, instale-o a partir de https://www.python.org/downloads/windows/
echo O instalador instala bibliotecas, mas nao instala automaticamente o proprio Python.
pause
exit /b 1
