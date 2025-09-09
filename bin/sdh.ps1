#!/usr/bin/env pwsh
# SD-Host CLI Launcher (PowerShell)
# Cross-platform PowerShell script for Windows, macOS, and Linux

param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$Arguments
)

# Get the directory where this script is located
$BinDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $BinDir

# Set environment variables
$env:PYTHONPATH = $ProjectRoot

# Determine Python executable based on platform
if ($IsWindows -or $env:OS -eq "Windows_NT") {
    # Windows
    $VenvPython = Join-Path $ProjectRoot "venv\Scripts\python.exe"
} else {
    # Unix/Linux/macOS
    $VenvPython = Join-Path $ProjectRoot "venv/bin/python"
}

# Check for Python executable in order of preference
if (Test-Path $VenvPython) {
    $PythonExe = $VenvPython
} elseif (Get-Command python3 -ErrorAction SilentlyContinue) {
    $PythonExe = "python3"
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    $PythonExe = "python"
} else {
    Write-Host "❌ Error: Python not found. Please install Python or create a virtual environment." -ForegroundColor Red
    exit 1
}

# Build CLI script path
$CLIScript = Join-Path $ProjectRoot "src\cli\sdh.py"

# Check if CLI script exists
if (-not (Test-Path $CLIScript)) {
    Write-Host "❌ Error: CLI script not found at: $CLIScript" -ForegroundColor Red
    exit 1
}

# Execute the CLI with all arguments
& $PythonExe $CLIScript @Arguments
