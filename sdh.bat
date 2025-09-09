@echo off
REM SD-Host CLI Tool - Root Directory Shortcut
REM This is a convenience shortcut that calls the CLI from the bin/ directory

REM Get the directory where this batch file is located (project root)
set "PROJECT_ROOT=%~dp0"

REM Remove trailing backslash if present
if "%PROJECT_ROOT:~-1%"=="\" set "PROJECT_ROOT=%PROJECT_ROOT:~0,-1%"

REM Call the actual CLI tool in the bin/ subdirectory
"%PROJECT_ROOT%\bin\sdh.bat" %*
