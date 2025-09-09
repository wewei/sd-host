# SD-Host CLI Tool

Command-line interface for managing SD-Host service and querying status.

## 📁 Directory Structure

```
src/cli/
├── sdh.py      # Main CLI implementation
└── README.md   # This documentation

bin/
├── sdh.bat     # Windows launcher
└── sdh         # Unix/Linux/macOS launcher
```

## 🚀 Usage

### From Project Root (Recommended)
```bash
# Windows
.\sdh.bat service status
.\sdh.bat models list

# Linux/macOS
./bin/sdh service status
./bin/sdh models list
```

### Direct from bin/ Directory
```bash
# Windows
.\bin\sdh.bat service status

# Linux/macOS  
./bin/sdh service status
```

### Global Access

To use `sdh` from anywhere:

**Windows**: Add the project root directory to your system PATH environment variable  
**Linux/macOS**: Add the `bin/` directory to your PATH or create a symlink

## 📋 Available Commands

### Service Management
- `sdh service status` - Show service status
- `sdh service start` - Start the service  
- `sdh service stop` - Stop the service
- `sdh service restart` - Restart the service

### Models Management
- `sdh models list` - List all models
- `sdh models status` - Show models overview

### Future Features
- `sdh images list` - List all images (coming soon)
- `sdh tasks list` - List all tasks (coming soon)
- `sdh tasks status` - Show tasks overview (coming soon)

## 🔧 Architecture

The CLI tool is designed with a modular architecture:

- **`SDHostCLI`** class: Main CLI management interface
- **Service Management**: Process monitoring with PID tracking
- **API Integration**: Real-time data from SD-Host REST API
- **Colored Output**: Professional terminal interface with status indicators
- **Cross-platform**: Python + Windows batch launcher

## 🛠️ Development

The CLI automatically detects the project structure:

- Project root is determined from CLI location (src/cli/ → project root)
- Virtual environment: `../../venv/Scripts/python.exe` (Windows) or `../../venv/bin/python` (Unix)
- Main service: `../../src/main.py`
- PID file: `../../.sdh.pid`
- Logs: `../../logs/sdh.log`

## 📝 Dependencies

The CLI requires the following Python packages:
- `psutil` - Process management
- `requests` - API communication
- `argparse` - Command-line parsing (built-in)
- `pathlib` - Path handling (built-in)
