#!/usr/bin/env pwsh
# SD-Host CLI Installation Script (PowerShell)
# Cross-platform installer for Windows, macOS, and Linux

param(
    [switch]$Uninstall,
    [switch]$Force,
    [switch]$Quiet
)

# Set output encoding to UTF-8 to handle special characters properly
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# Function to write colored output safely
function Write-SafeHost {
    param($Message, $Color = "White")
    try {
        Write-Host $Message -ForegroundColor $Color
    } catch {
        Write-Host $Message
    }
}

function Write-Title {
    param($Message)
    Write-SafeHost $Message "Cyan"
}

function Write-Success {
    param($Message)
    Write-SafeHost "[SUCCESS] $Message" "Green"
}

function Write-Error {
    param($Message)
    Write-SafeHost "[ERROR] $Message" "Red"
}

function Write-Warning {
    param($Message)
    Write-SafeHost "[WARNING] $Message" "Yellow"
}

function Write-Info {
    param($Message)
    Write-SafeHost "[INFO] $Message" "Cyan"
}

# Get script directory and project root
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
$BinDir = $ScriptDir

if (-not $Quiet) {
    Write-Title "SD-Host CLI Installation Script"
    Write-Title "================================"
    Write-Host ""
}

# Detect platform
if ($IsWindows -or $env:OS -eq "Windows_NT") {
    $Platform = "Windows"
    $PathSeparator = ";"
    $MainScript = "sdh.bat"
} elseif ($IsMacOS) {
    $Platform = "macOS" 
    $PathSeparator = ":"
    $MainScript = "sdh"
} elseif ($IsLinux) {
    $Platform = "Linux"
    $PathSeparator = ":"
    $MainScript = "sdh"
} else {
    $Platform = "Unix"
    $PathSeparator = ":"
    $MainScript = "sdh"
}

if (-not $Quiet) {
    Write-Info "Platform: $Platform"
    Write-Info "Project root: $ProjectRoot"
    Write-Info "Bin directory: $BinDir"
    Write-Host ""
}

# Function to check if directory is in PATH
function Test-InPath {
    param($Directory)
    
    if ($Platform -eq "Windows") {
        $CurrentPath = [Environment]::GetEnvironmentVariable("PATH", "User")
    } else {
        $CurrentPath = $env:PATH
    }
    
    if (-not $CurrentPath) { return $false }
    return ($CurrentPath -split $PathSeparator | Where-Object { $_ -eq $Directory }).Count -gt 0
}

# Function to add directory to PATH
function Add-ToPath {
    param($Directory)
    
    if ($Platform -eq "Windows") {
        # Windows - modify user PATH
        $CurrentPath = [Environment]::GetEnvironmentVariable("PATH", "User")
        if (-not $CurrentPath) { $CurrentPath = "" }
        
        # Remove existing entry if present
        $PathEntries = $CurrentPath -split ";" | Where-Object { $_ -ne "" -and $_ -ne $Directory }
        $NewPath = ($PathEntries + $Directory) -join ";"
        
        [Environment]::SetEnvironmentVariable("PATH", $NewPath, "User")
        $env:PATH = [Environment]::GetEnvironmentVariable("PATH", "Machine") + ";" + $NewPath
        
        Write-Success "Added to user PATH: $Directory"
        if (-not $Quiet) {
            Write-Warning "Please restart your terminal for changes to take effect"
        }
    } else {
        # Unix/Linux/macOS - add to shell profiles
        $ShellProfiles = @()
        if (Test-Path "$env:HOME/.bashrc") { $ShellProfiles += "$env:HOME/.bashrc" }
        if (Test-Path "$env:HOME/.zshrc") { $ShellProfiles += "$env:HOME/.zshrc" }
        if (Test-Path "$env:HOME/.profile") { $ShellProfiles += "$env:HOME/.profile" }
        
        $ExportLine = "export PATH=`"$Directory`$PathSeparator`$PATH`""
        $Added = $false
        
        foreach ($Profile in $ShellProfiles) {
            $Content = Get-Content $Profile -Raw -ErrorAction SilentlyContinue
            if (-not $Content -or $Content -notmatch [regex]::Escape($Directory)) {
                Add-Content $Profile "`n# SD-Host CLI`n$ExportLine"
                Write-Success "Added to $Profile"
                $Added = $true
            }
        }
        
        if (-not $Added -and $ShellProfiles.Count -eq 0) {
            # Create .profile if no shell profiles exist
            Add-Content "$env:HOME/.profile" "# SD-Host CLI`n$ExportLine"
            Write-Success "Created and added to ~/.profile"
        }
        
        # Update current session
        $env:PATH = "$Directory$PathSeparator$env:PATH"
        Write-Success "Added to current session PATH"
        if (-not $Quiet) {
            Write-Warning "Please restart your terminal or run: source ~/.bashrc (or ~/.zshrc)"
        }
    }
}

# Function to remove directory from PATH
function Remove-FromPath {
    param($Directory)
    
    if ($Platform -eq "Windows") {
        $CurrentPath = [Environment]::GetEnvironmentVariable("PATH", "User")
        if ($CurrentPath) {
            $PathEntries = $CurrentPath -split ";" | Where-Object { $_ -ne "" -and $_ -ne $Directory }
            $NewPath = $PathEntries -join ";"
            [Environment]::SetEnvironmentVariable("PATH", $NewPath, "User")
            Write-Success "Removed from user PATH: $Directory"
        }
    } else {
        $ShellProfiles = @(
            "$env:HOME/.bashrc",
            "$env:HOME/.zshrc",
            "$env:HOME/.profile"
        )
        
        foreach ($Profile in $ShellProfiles) {
            if (Test-Path $Profile) {
                $Content = Get-Content $Profile -Raw -ErrorAction SilentlyContinue
                if ($Content -and $Content -match [regex]::Escape($Directory)) {
                    $UpdatedContent = $Content -replace "(?m)^# SD-Host CLI\s*\n.*$Directory.*\n?", ""
                    Set-Content $Profile $UpdatedContent
                    Write-Success "Removed from $Profile"
                }
            }
        }
    }
}

# Main installation logic
if ($Uninstall) {
    if (-not $Quiet) {
        Write-Info "Uninstalling SD-Host CLI..."
    }
    
    if (Test-InPath $BinDir) {
        Remove-FromPath $BinDir
        Write-Success "SD-Host CLI removed from PATH"
    } else {
        Write-Warning "SD-Host CLI was not found in PATH"
    }
    
    if (-not $Quiet) {
        Write-Info "Uninstallation complete"
    }
} else {
    if (-not $Quiet) {
        Write-Info "Installing SD-Host CLI..."
    }
    
    # Check if bin directory exists
    if (-not (Test-Path $BinDir)) {
        Write-Error "Bin directory not found: $BinDir"
        exit 1
    }
    
    # Check if main script exists
    $MainScriptPath = Join-Path $BinDir $MainScript
    if (-not (Test-Path $MainScriptPath)) {
        Write-Error "Main script not found: $MainScriptPath"
        exit 1
    }
    
    # Check if already in PATH
    if (Test-InPath $BinDir) {
        if ($Force) {
            if (-not $Quiet) {
                Write-Info "Directory already in PATH, reinstalling..."
            }
            Remove-FromPath $BinDir
            Add-ToPath $BinDir
        } else {
            Write-Warning "Directory already in PATH: $BinDir"
            if (-not $Quiet) {
                Write-Info "Use -Force to reinstall"
            }
            exit 0
        }
    } else {
        Add-ToPath $BinDir
    }
    
    # Test the CLI
    if (-not $Quiet) {
        Write-Info "Testing CLI installation..."
        try {
            $TestResult = & $MainScriptPath --version 2>&1
            if ($LASTEXITCODE -eq 0) {
                Write-Success "CLI test successful"
            } else {
                Write-Warning "CLI test failed (exit code: $LASTEXITCODE)"
            }
        } catch {
            Write-Warning "CLI test failed: $_"
        }
    }
    
    Write-Success "SD-Host CLI installed successfully!"
    
    if (-not $Quiet) {
        Write-Host ""
        Write-Title "Quick Start:"
        Write-Host "  $MainScript --help          # Show help"
        Write-Host "  $MainScript --version       # Show version" 
        Write-Host "  $MainScript service status  # Check service status"
        Write-Host "  $MainScript config show     # Show configuration"
        Write-Host ""
    }
}
