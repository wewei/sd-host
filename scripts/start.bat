@echo off
REM SD-Host startup script for Windows

echo SD-Host: Stable Diffusion RESTful API Service
echo Starting up...

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Check if virtual environment exists
if not exist "venv" (
    echo Virtual environment not found. Creating...
    python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies if requirements.txt exists
if exist "requirements\requirements.txt" (
    echo Installing dependencies...
    pip install -r requirements\requirements.txt
)

REM Create necessary directories
if not exist "models" mkdir models
if not exist "output" mkdir output
if not exist "data" mkdir data
if not exist "logs" mkdir logs

REM Check if config file exists
if not exist "config\config.yml" (
    echo Config file not found. Copying from example...
    copy "config\config.example.yml" "config\config.yml"
    echo Please edit config\config.yml before running the service
)

REM Start the service
echo Starting SD-Host service...
python src\main.py

pause
