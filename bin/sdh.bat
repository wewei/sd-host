@echo off
REM SD-Host CLI Tool Launcher
REM This batch file allows you to run 'sdh' from anywhere

REM Get the directory where this batch file is located (bin/)
set "BIN_DIR=%~dp0"

REM Remove trailing backslash if present
if "%BIN_DIR:~-1%"=="\" set "BIN_DIR=%BIN_DIR:~0,-1%"

REM Go to parent directory (project root)
set "PROJECT_ROOT=%BIN_DIR%\.."

REM Use the virtual environment Python to run the CLI
"%PROJECT_ROOT%\venv\Scripts\python.exe" "%PROJECT_ROOT%\src\cli\sdh.py" %*
