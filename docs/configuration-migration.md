# Configuration Migration Guide

## SD-Host Configuration System Overhaul

SD-Host has been updated with a new, more flexible configuration management system. This guide will help you migrate from the old system to the new one.

## What's New

### 1. Depot Concept
- **Depot**: A single root directory containing all SD-Host data
- **Default Location**: `~/sd-host/depot`
- **Environment Variable**: `SDH_DEPOT` to override default location
- **CLI Option**: `--depot` or `-d` to specify depot location

### 2. Unified Configuration
- **Configuration File**: `~/sd-host/config.yml` (user-specific)
- **No More .env Files**: All configuration now in YAML format
- **No More Project Config**: Old `config/config.yml` is no longer used

### 3. Directory Structure
```
~/sd-host/
├── config.yml          # Configuration file
└── depot/               # Data depot (or custom location)
    ├── models/          # Model files
    ├── output/          # Generated images
    ├── data/            # Database and app data
    └── logs/            # Application logs
```

## Migration Steps

### Step 1: Initialize New Configuration
```bash
# Initialize configuration with default settings
sdh config init

# Or initialize with custom depot location
sdh --depot /path/to/my/depot config init
```

### Step 2: Migrate Your Settings
If you had custom settings in the old `config/config.yml` or `.env` files, you'll need to transfer them to the new `~/sd-host/config.yml`.

**Old `.env` format:**
```bash
SD_HOST_PORT=9000
SD_HOST_DEBUG=true
SD_OUTPUT_DIR=./custom_output
```

**New `config.yml` format:**
```yaml
server:
  port: 9000
  debug: true

# output_dir is now auto-set to {depot}/output
# but you can still override it:
storage:
  output_dir: "/path/to/custom/output"
```

### Step 3: Update Your Scripts
If you had scripts or services that used the old configuration:

**Old approach:**
```bash
# Scripts had to be run from project directory
cd /path/to/sd-host
python src/api/main.py
```

**New approach:**
```bash
# Can run from anywhere, depot location is configurable
SDH_DEPOT=/my/depot python -m sd_host.api.main

# Or use CLI
sdh --depot /my/depot service start
```

## CLI Changes

### New Global Options
```bash
# Specify depot location
sdh --depot /path/to/depot service start

# Use custom config file
sdh --config /path/to/config.yml service start

# Show current configuration
sdh config show

# Show config file location
sdh config path

# Initialize new configuration
sdh config init
```

### Environment Variables
- `SDH_DEPOT`: Override default depot location
- Old `.env` files are no longer used

## Configuration Reference

### Complete Configuration Example
```yaml
# ~/sd-host/config.yml

app_name: "SD-Host"
app_version: "0.1.0"

server:
  host: "0.0.0.0"
  port: 8000
  debug: false
  workers: 1

stable_diffusion:
  model_name: "runwayml/stable-diffusion-v1-5"
  device: "auto"
  precision: "fp16"
  default_width: 512
  default_height: 512

storage:
  # depot_dir is auto-detected, but can be overridden
  depot_dir: "/custom/depot/path"
  
  # These are auto-set relative to depot_dir, but can be overridden
  # models_dir: "/custom/models"
  # output_dir: "/custom/output"
  # data_dir: "/custom/data"

api:
  rate_limit_requests: 10
  cors_origins: ["*"]

civitai:
  api_key: "your-api-key"
  base_url: "https://civitai.com/api/v1"

proxy:
  http_proxy: "http://proxy.example.com:8080"
  https_proxy: "https://proxy.example.com:8080"

logging:
  level: "INFO"
  format: "structured"
  # log file is auto-set to {depot}/logs/sd_host.log

security:
  api_key_enabled: false
  ssl_enabled: false

monitoring:
  health_check_enabled: true
  metrics_enabled: false

file:
  max_file_size: 10737418240  # 10GB
  allowed_extensions: [".safetensors", ".ckpt", ".pt"]
```

## Troubleshooting

### Configuration Not Found
If you get "configuration not found" errors:
```bash
# Check current config location
sdh config path

# Initialize new configuration
sdh config init
```

### Permission Issues
If you get permission errors:
```bash
# Make sure you have write access to the config directory
ls -la ~/sd-host/

# Check depot directory permissions
sdh config show
```

### Migration from Docker
If you were using Docker with volume mounts:
```bash
# Old Docker approach
docker run -v ./models:/app/models -v ./output:/app/output sd-host

# New Docker approach (example)
docker run -v /host/depot:/depot -e SDH_DEPOT=/depot sd-host
```

## Benefits of New System

1. **Flexible Location**: Depot can be anywhere (external drives, network storage)
2. **User-Specific Config**: No more project-specific config files
3. **Environment Override**: Easy to switch between environments
4. **CLI Integration**: Built-in configuration management
5. **Consistent Paths**: All data in one organized location
6. **Better Defaults**: Sensible defaults that work out of the box

## Getting Help

```bash
# Show detailed help
sdh --help

# Show configuration
sdh config show

# Test your setup
sdh service status
```
