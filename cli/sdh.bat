@echo off
REM SD-Host CLI Tool Launcher
REM This batch file allows you to run 'sdh' from anywhere

REM Get the directory where this batch file is located
set "SDH_ROOT=%~dp0"

REM Remove trailing backslash if present
if "%SDH_ROOT:~-1%"=="\" set "SDH_ROOT=%SDH_ROOT:~0,-1%"

REM Go to parent directory (project root)
set "PROJECT_ROOT=%SDH_ROOT%\.."

REM Use the virtual environment Python to run the CLI
"%PROJECT_ROOT%\venv\Scripts\python.exe" "%SDH_ROOT%\sdh.py" %*
