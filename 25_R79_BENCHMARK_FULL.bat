@echo off
set R79_FULL=1
set R79_LOCAL_STEPS=600
set R79_COORD_STEPS=1000
set R79_INFER_REPEATS=10
call "%~dp0RUN_PYTHON.bat" r79_benchmark.py
pause
