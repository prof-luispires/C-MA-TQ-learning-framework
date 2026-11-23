@echo off
set R81_FULL=1
set R81_LOCAL_STEPS=600
set R81_COORD_STEPS=1000
call "%~dp0RUN_PYTHON.bat" r81_structural_diagnostic.py
pause
