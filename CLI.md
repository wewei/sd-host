# SD-Host CLI Tools

This directory contains the command-line interface tools for SD-Host.

## 📁 Directory Structure

```
bin/                    # Executable scripts
├── sdh.bat            # Windows launcher
└── sdh                # Unix/Linux/macOS launcher

src/cli/               # CLI implementation
├── sdh.py            # Main CLI Python code
└── README.md         # Detailed CLI documentation

sdh.bat               # Root convenience shortcut (Windows)
```

## 🚀 Quick Start

### Windows
```bash
# From project root (recommended)
.\sdh.bat service status

# Direct from bin/
.\bin\sdh.bat service status
```

### Linux/macOS
```bash
# From project root
./bin/sdh service status

# Make globally available (optional)
sudo ln -s $(pwd)/bin/sdh /usr/local/bin/sdh
```

## 📖 Documentation

For detailed usage instructions, see [`src/cli/README.md`](src/cli/README.md).

## 🏗️ Architecture

- **`bin/`**: Contains platform-specific launcher scripts that handle path resolution and virtual environment activation
- **`src/cli/`**: Contains the actual Python implementation and documentation
- **Root shortcut**: Provides convenience access from project root

This separation follows Unix conventions where:
- `bin/` contains executable scripts
- `src/` contains source code
- Platform differences are handled at the launcher level
