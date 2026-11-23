@echo off
rem Devolve PYTHON_EXE com um interpretador valido (nao um alias da Microsoft Store).
set "PYTHON_EXE="
for /f "delims=" %%P in ('py -3 -c "import sys; print(sys.executable)" 2^>nul') do if not defined PYTHON_EXE set "PYTHON_EXE=%%P"
if defined PYTHON_EXE goto :validate
for /f "delims=" %%P in ('python -c "import sys; print(sys.executable)" 2^>nul') do if not defined PYTHON_EXE set "PYTHON_EXE=%%P"
if defined PYTHON_EXE goto :validate
for %%P in ("%LOCALAPPDATA%\Programs\Thonny\python.exe" "%ProgramFiles%\Thonny\python.exe" "%ProgramFiles(x86)%\Thonny\python.exe" "%LOCALAPPDATA%\Programs\Python\Python313\python.exe" "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" "%LOCALAPPDATA%\Programs\Python\Python314\python.exe") do if not defined PYTHON_EXE if exist "%%~P" set "PYTHON_EXE=%%~P"
if not defined PYTHON_EXE (
 echo ERRO: Python nao encontrado via py, python ou localizacoes habituais do Thonny.
 echo Instale Python 3.11 ou superior: https://www.python.org/downloads/windows/
 exit /b 1
)
:validate
"%PYTHON_EXE%" -c "import sys; assert sys.version_info >= (3, 11), 'Requer Python 3.11+'" >nul 2>&1
if errorlevel 1 (
 echo ERRO: Python encontrado mas a versao e inferior a 3.11.
 exit /b 1
)
echo Python encontrado: "%PYTHON_EXE%"
exit /b 0
