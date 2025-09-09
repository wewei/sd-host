@echo off
REM SD-Host CLI Tool - Root Directory Shortcut
REM This is a convenience shortcut that calls the CLI from the cli/ directory

REM Get the directory where this batch file is located (project root)
set "PROJECT_ROOT=%~dp0"

REM Remove trailing backslash if present
if "%PROJECT_ROOT:~-1%"=="\" set "PROJECT_ROOT=%PROJECT_ROOT:~0,-1%"

REM Call the actual CLI tool in the cli/ subdirectory
"%PROJECT_ROOT%\cli\sdh.bat" %*
