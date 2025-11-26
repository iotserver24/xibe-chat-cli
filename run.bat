@echo off
REM Run XIBE-CHAT CLI with the virtual environment Python
cd /d "%~dp0"

REM Use the Python from the virtual environment
if exist ".venv\Scripts\python.exe" (
    echo Running in virtual environment...
    .venv\Scripts\python.exe ai_cli.py
    exit /b %ERRORLEVEL%
) else (
    echo Error: Virtual environment not found!
    echo Please create a virtual environment first:
    echo   python -m venv .venv
    echo   .venv\Scripts\python.exe -m pip install -r requirements.txt
    exit /b 1
)

