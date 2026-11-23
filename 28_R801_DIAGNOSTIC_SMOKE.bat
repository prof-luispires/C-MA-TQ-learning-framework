@echo off
set R80_FULL=0
set R80_LOCAL_STEPS=100
set R80_COORD_STEPS=180
call "%~dp0RUN_PYTHON.bat" r80_structural_diagnostic.py
pause
