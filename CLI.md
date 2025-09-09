# SD-Host CLI Tools

A modern, beautiful command-line interface for SD-Host built with Typer and Rich.

## 📁 Directory Structure

```
bin/                    # Executable scripts and installers
├── sdh.bat            # Windows launcher
├── sdh                # Unix/Linux/macOS launcher  
├── sdh.ps1            # PowerShell script (cross-platform)
├── install.ps1        # PowerShell installer (cross-platform)
└── install.sh         # Bash installer (Unix/Linux/macOS)

src/cli/               # CLI implementation
├── main.py           # Main Typer application
├── sdh.py            # Entry point
├── utils.py          # Shared utilities and Rich formatting
└── commands/         # Modular command structure
    ├── config.py     # Configuration management
    ├── service.py    # Service control
    ├── models.py     # Model management
    ├── images.py     # Image operations
    └── tasks.py      # Task management
```

## 🚀 Installation

### Automatic Installation (Recommended)

Run the appropriate installation script for your platform:

**Windows (PowerShell):**

```powershell
# From project root
.\bin\install.ps1

# With options
.\bin\install.ps1 -Force    # Force reinstall
.\bin\install.ps1 -Quiet    # Silent installation
```

**Unix/Linux/macOS (Bash):**

```bash
# From project root  
./bin/install.sh

# With options
./bin/install.sh --force     # Force reinstall
./bin/install.sh --quiet     # Silent installation
./bin/install.sh --uninstall # Remove from PATH
```

### Manual Usage

**Windows:**

```powershell
# Batch script (Windows native)
.\bin\sdh.bat --help

# PowerShell script (cross-platform)
.\bin\sdh.ps1 --help
```

**Unix/Linux/macOS:**

```bash
# Shell script
./bin/sdh --help

# PowerShell script (if PowerShell Core is installed)
./bin/sdh.ps1 --help
```

## 📖 Usage Guide

### Basic Commands

```bash
# Show help with beautiful formatting
sdh --help

# Show version
sdh --version

# Show system information
sdh info
```

### Service Management

```bash
# Check service status (displays in Rich table)
sdh service status

# Start the service
sdh service start

# Stop the service
sdh service stop

# Restart the service
sdh service restart

# View service logs
sdh service logs

# Follow logs in real-time
sdh service logs --follow
```

### Configuration Management

```bash
# Show all configuration (formatted table)
sdh config show

# Get specific configuration value
sdh config get server.port
sdh config get server.debug

# Set configuration value
sdh config set server.port 9000
sdh config set server.debug true

# Show configuration file path
sdh config path

# Initialize configuration file
sdh config init
```

### Models Management

```bash
# List all models (Rich table with pagination)
sdh models list

# Show models overview
sdh models status

# List with limit
sdh models list --limit 5

# Filter by type
sdh models list --type checkpoint
```

### Advanced Usage

```bash
# Use custom depot location
sdh --depot /path/to/depot config show

# Use custom configuration file
sdh --config /path/to/config.yml service start

# Verbose output
sdh --verbose service status
```

## 🎨 Features

- **Beautiful Output**: Rich tables, colors, and formatting
- **Type Safety**: Typer provides automatic validation and help generation
- **Modular Design**: Commands organized in separate modules
- **Auto-completion**: Shell completion support (where available)
- **Error Handling**: Helpful error messages with context
- **Configuration**: Flexible config management with depot support

## 🏗️ Architecture

The CLI follows modern Python CLI patterns:

- **Typer Framework**: Modern CLI library with automatic help generation
- **Rich Terminal**: Beautiful formatting, tables, and progress bars
- **Modular Commands**: Each command group in separate files
- **Shared State**: CLIState class manages configuration and context
- **Entry Points**: Multiple ways to access the CLI for flexibility

## 🔧 Environment Variables

- `SDH_DEPOT` - Override default depot location
- Set via command line: `$env:SDH_DEPOT="D:\my-depot"; sdh config show`

## 📍 Configuration

The CLI automatically manages configuration at:

- Configuration file: `~/sd-host/config.yml`
- Default depot: `~/sd-host/depot`

## 🛠️ Troubleshooting

### CLI Not Found

```bash
# Check if bin directory is in PATH
echo $env:PATH

# Run installation script
.\install.ps1

# Or use full path
.\bin\sdh.bat --help
```

### Service Issues

```bash
# Check service status
sdh service status

# View recent logs with colors
sdh service logs --lines 20

# Check configuration
sdh config show
```

### Configuration Issues

```bash
# Show configuration file location
sdh config path

# Reinitialize configuration
sdh config init --force
```

This CLI provides a professional, user-friendly interface to SD-Host with modern terminal aesthetics and powerful functionality.
