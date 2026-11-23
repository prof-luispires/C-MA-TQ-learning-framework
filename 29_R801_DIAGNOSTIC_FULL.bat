@echo off
set R80_FULL=1
set R80_LOCAL_STEPS=600
set R80_COORD_STEPS=1000
call "%~dp0RUN_PYTHON.bat" r80_structural_diagnostic.py
pause
