# SD-Host CLI Executables

This directory contains all executable scripts and installers for the SD-Host CLI.

## 📂 Files

### Launchers
- **`sdh.bat`** - Windows batch script launcher
- **`sdh`** - Unix/Linux/macOS shell script launcher  
- **`sdh.ps1`** - Cross-platform PowerShell script launcher

### Installers
- **`install.ps1`** - Cross-platform PowerShell installer (Windows/macOS/Linux)
- **`install.sh`** - Unix/Linux/macOS bash installer

## 🚀 Quick Start

### Installation

**Windows:**
```powershell
.\install.ps1
```

**Unix/Linux/macOS:**
```bash
./install.sh
```

### Usage After Installation

Once installed, you can use the CLI from anywhere:

```bash
# On Windows
sdh --help

# On Unix/Linux/macOS  
sdh --help

# PowerShell (any platform)
sdh.ps1 --help
```

### Manual Usage (Without Installation)

**Windows:**
```powershell
# From project root
.\bin\sdh.bat --help
.\bin\sdh.ps1 --help
```

**Unix/Linux/macOS:**
```bash
# From project root
./bin/sdh --help
./bin/sdh.ps1 --help  # If PowerShell Core is installed
```

## 🔧 Platform Support

| Platform | Batch | Shell | PowerShell |
|----------|-------|-------|------------|
| Windows  | ✅ `sdh.bat` | ❌ | ✅ `sdh.ps1` |
| macOS    | ❌ | ✅ `sdh` | ✅ `sdh.ps1` |
| Linux    | ❌ | ✅ `sdh` | ✅ `sdh.ps1` |

## 📝 Installation Options

### PowerShell Installer (`install.ps1`)
```powershell
.\install.ps1           # Standard installation
.\install.ps1 -Force    # Force reinstall
.\install.ps1 -Quiet    # Silent installation
.\install.ps1 -Uninstall # Remove from PATH
```

### Bash Installer (`install.sh`)
```bash
./install.sh           # Standard installation
./install.sh --force   # Force reinstall  
./install.sh --quiet   # Silent installation
./install.sh --uninstall # Remove from PATH
./install.sh --help    # Show help
```

## 🔍 What the Installers Do

1. **Detect Platform** - Automatically detect Windows/macOS/Linux
2. **Add to PATH** - Add the bin directory to your system PATH
3. **Update Shell Profiles** - Modify `.bashrc`, `.zshrc`, `.profile` (Unix/Linux/macOS)
4. **Update Registry** - Modify user PATH environment variable (Windows)
5. **Test Installation** - Verify CLI works after installation

## 🛠️ Technical Details

### Path Resolution
All scripts automatically detect:
- Project root directory
- Python virtual environment location
- CLI entry point location

### Virtual Environment Support
The launchers automatically detect and use:
- Windows: `venv\Scripts\python.exe`
- Unix/Linux/macOS: `venv/bin/python`
- Fallback: System Python (`python3` or `python`)

### Cross-Platform Compatibility
- **PowerShell scripts** work on Windows PowerShell 5.1+ and PowerShell Core 6.0+
- **Shell scripts** work on bash, zsh, and other POSIX-compatible shells
- **Batch scripts** work on Windows Command Prompt and PowerShell
