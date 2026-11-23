@echo off
set R79_LOCAL_STEPS=100
set R79_COORD_STEPS=180
set R79_INFER_REPEATS=5
call "%~dp0RUN_PYTHON.bat" r79_benchmark.py
pause
