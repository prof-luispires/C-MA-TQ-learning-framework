@echo off
set R81_FULL=0
set R81_LOCAL_STEPS=100
set R81_COORD_STEPS=180
call "%~dp0RUN_PYTHON.bat" r81_structural_diagnostic.py
pause
