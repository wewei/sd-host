#!/usr/bin/env python3
"""
SD-Host CLI Tool (sdh)
Command-line interface for managing SD-Host service and querying status
"""

import os
import sys
import json
import time
import psutil
import argparse
import subprocess
from pathlib import Path
from typing import Dict, List, Optional
import requests
from datetime import datetime

# Add src to Python path for imports (CLI is in src/cli/ subdirectory)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.config import get_settings, reload_settings, get_config_file_path

class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    END = '\033[0m'

class SDHostCLI:
    """SD-Host CLI management tool"""
    
    def __init__(self, depot_dir: Optional[str] = None, config_path: Optional[str] = None):
        # CLI is in src/cli/ subdirectory, so project root is two levels up
        self.project_dir = Path(__file__).parent.parent.parent.absolute()
        self.python_exe = self.project_dir / "venv" / "Scripts" / "python.exe"
        self.main_script = self.project_dir / "src" / "api" / "main.py"
        
        # Load configuration with depot override
        self.settings = get_settings(config_path, depot_dir)
        
        # Set up paths based on configuration
        self.pid_file = Path(self.settings.depot_dir) / ".sdh.pid"
        self.log_file = Path(self.settings.logging.file)
        self.api_base = f"http://{self.settings.host}:{self.settings.port}"
        
        # Ensure directories exist
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        Path(self.settings.depot_dir).mkdir(parents=True, exist_ok=True)
    
    def print_status(self, message: str, status: str = "info"):
        """Print colored status message"""
        colors = {
            "info": Colors.BLUE,
            "success": Colors.GREEN,
            "warning": Colors.YELLOW,
            "error": Colors.RED,
            "header": Colors.CYAN + Colors.BOLD
        }
        color = colors.get(status, Colors.WHITE)
        print(f"{color}{message}{Colors.END}")
    
    def print_header(self, text: str):
        """Print header with decorative lines"""
        self.print_status("=" * 60, "header")
        self.print_status(f" {text} ", "header")
        self.print_status("=" * 60, "header")
    
    def is_service_running(self) -> Optional[int]:
        """Check if SD-Host service is running, return PID if found"""
        if not self.pid_file.exists():
            return None
        
        try:
            with open(self.pid_file, 'r') as f:
                pid = int(f.read().strip())
            
            # Check if process exists and is our python process
            if psutil.pid_exists(pid):
                proc = psutil.Process(pid)
                if 'python' in proc.name().lower() and 'main.py' in ' '.join(proc.cmdline()):
                    return pid
            
            # PID file exists but process is not running, clean up
            self.pid_file.unlink()
            return None
            
        except (ValueError, psutil.NoSuchProcess, PermissionError):
            return None
    
    def get_service_status(self) -> Dict:
        """Get comprehensive service status"""
        pid = self.is_service_running()
        
        if not pid:
            return {
                "running": False,
                "pid": None,
                "uptime": None,
                "memory": None,
                "cpu": None,
                "api_accessible": False
            }
        
        try:
            proc = psutil.Process(pid)
            create_time = datetime.fromtimestamp(proc.create_time())
            uptime = datetime.now() - create_time
            
            # Check API accessibility
            api_accessible = False
            try:
                response = requests.get(f"{self.api_base}/health", timeout=5)
                api_accessible = response.status_code == 200
            except:
                pass
            
            return {
                "running": True,
                "pid": pid,
                "uptime": str(uptime).split('.')[0],  # Remove microseconds
                "memory": f"{proc.memory_info().rss / 1024 / 1024:.1f} MB",
                "cpu": f"{proc.cpu_percent():.1f}%",
                "api_accessible": api_accessible
            }
            
        except psutil.NoSuchProcess:
            return {
                "running": False,
                "pid": None,
                "uptime": None,
                "memory": None,
                "cpu": None,
                "api_accessible": False
            }
    
    def start_service(self) -> bool:
        """Start SD-Host service"""
        if self.is_service_running():
            self.print_status("❌ Service is already running", "error")
            return False
        
        if not self.python_exe.exists():
            self.print_status("❌ Python virtual environment not found", "error")
            self.print_status(f"Expected: {self.python_exe}", "info")
            return False
        
        if not self.main_script.exists():
            self.print_status("❌ Main script not found", "error")
            self.print_status(f"Expected: {self.main_script}", "info")
            return False
        
        self.print_status("🚀 Starting SD-Host service...", "info")
        
        try:
            # Start process in background
            process = subprocess.Popen(
                [str(self.python_exe), str(self.main_script)],
                stdout=open(self.log_file, 'w'),
                stderr=subprocess.STDOUT,
                cwd=str(self.project_dir),
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
            )
            
            # Save PID
            with open(self.pid_file, 'w') as f:
                f.write(str(process.pid))
            
            # Wait a moment and check if it started successfully
            time.sleep(3)
            
            if self.is_service_running():
                self.print_status("✅ Service started successfully", "success")
                self.print_status(f"📝 Logs: {self.log_file}", "info")
                
                # Wait for API to be accessible
                self.print_status("⏳ Waiting for API to be ready...", "info")
                for i in range(10):
                    try:
                        response = requests.get(f"{self.api_base}/health", timeout=2)
                        if response.status_code == 200:
                            self.print_status("🌐 API is accessible", "success")
                            break
                    except:
                        pass
                    time.sleep(1)
                else:
                    self.print_status("⚠️  Service started but API may not be ready yet", "warning")
                
                return True
            else:
                self.print_status("❌ Failed to start service", "error")
                return False
                
        except Exception as e:
            self.print_status(f"❌ Error starting service: {e}", "error")
            return False
    
    def stop_service(self) -> bool:
        """Stop SD-Host service"""
        pid = self.is_service_running()
        
        if not pid:
            self.print_status("❌ Service is not running", "error")
            return False
        
        self.print_status(f"🛑 Stopping SD-Host service (PID: {pid})...", "info")
        
        try:
            proc = psutil.Process(pid)
            proc.terminate()
            
            # Wait for graceful shutdown
            try:
                proc.wait(timeout=10)
            except psutil.TimeoutExpired:
                self.print_status("⚠️  Forcing shutdown...", "warning")
                proc.kill()
                proc.wait(timeout=5)
            
            # Clean up PID file
            if self.pid_file.exists():
                self.pid_file.unlink()
            
            self.print_status("✅ Service stopped successfully", "success")
            return True
            
        except psutil.NoSuchProcess:
            self.print_status("❌ Process not found", "error")
            if self.pid_file.exists():
                self.pid_file.unlink()
            return False
        except Exception as e:
            self.print_status(f"❌ Error stopping service: {e}", "error")
            return False
    
    def restart_service(self) -> bool:
        """Restart SD-Host service"""
        self.print_status("🔄 Restarting SD-Host service...", "info")
        
        if self.is_service_running():
            if not self.stop_service():
                return False
            time.sleep(2)
        
        return self.start_service()
    
    def show_service_status(self):
        """Display detailed service status"""
        self.print_header("SD-Host Service Status")
        
        status = self.get_service_status()
        
        if status["running"]:
            self.print_status("🟢 Status: RUNNING", "success")
            self.print_status(f"🆔 PID: {status['pid']}", "info")
            self.print_status(f"⏰ Uptime: {status['uptime']}", "info")
            self.print_status(f"💾 Memory: {status['memory']}", "info")
            self.print_status(f"🔥 CPU: {status['cpu']}", "info")
            
            if status["api_accessible"]:
                self.print_status("🌐 API: Accessible", "success")
                self.print_status(f"📡 URL: {self.api_base}", "info")
            else:
                self.print_status("🌐 API: Not accessible", "error")
        else:
            self.print_status("🔴 Status: STOPPED", "error")
        
        print()
    
    def api_request(self, endpoint: str) -> Optional[Dict]:
        """Make API request to SD-Host service"""
        if not self.is_service_running():
            self.print_status("❌ Service is not running", "error")
            return None
        
        try:
            response = requests.get(f"{self.api_base}{endpoint}", timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                self.print_status(f"❌ API error: {response.status_code}", "error")
                return None
        except requests.exceptions.RequestException as e:
            self.print_status(f"❌ Connection error: {e}", "error")
            return None
    
    def show_models_list(self):
        """Display list of models"""
        self.print_header("Models List")
        
        data = self.api_request("/api/models")
        if not data:
            return
        
        models = data.get("data", [])
        
        if not models:
            self.print_status("📭 No models found", "info")
            return
        
        for model in models:
            attrs = model.get("attributes", {})
            name = attrs.get("name", "Unknown")
            model_type = attrs.get("model_type", "unknown")
            size = attrs.get("size", 0)
            status = attrs.get("status", "unknown")
            
            size_mb = size / (1024 * 1024) if size else 0
            
            # Status color
            status_color = "success" if status == "ready" else "warning"
            
            print(f"{Colors.CYAN}📦 {name}{Colors.END}")
            print(f"   Type: {model_type} | Size: {size_mb:.1f} MB | Status: {self._colored_status(status)}")
            print()
    
    def show_models_status(self):
        """Display models status overview"""
        self.print_header("Models Status Overview")
        
        data = self.api_request("/api/models")
        if not data:
            return
        
        models = data.get("data", [])
        total = len(models)
        
        if total == 0:
            self.print_status("📭 No models found", "info")
            return
        
        # Count by status
        status_counts = {}
        type_counts = {}
        total_size = 0
        
        for model in models:
            attrs = model.get("attributes", {})
            status = attrs.get("status", "unknown")
            model_type = attrs.get("model_type", "unknown")
            size = attrs.get("size", 0)
            
            status_counts[status] = status_counts.get(status, 0) + 1
            type_counts[model_type] = type_counts.get(model_type, 0) + 1
            total_size += size
        
        # Display summary
        self.print_status(f"📊 Total Models: {total}", "info")
        self.print_status(f"💾 Total Size: {total_size / (1024**3):.2f} GB", "info")
        print()
        
        self.print_status("📈 By Status:", "header")
        for status, count in status_counts.items():
            print(f"   {self._colored_status(status)}: {count}")
        print()
        
        self.print_status("🏷️  By Type:", "header")
        for model_type, count in type_counts.items():
            print(f"   {model_type}: {count}")
        print()
    
    def show_tasks_list(self):
        """Display list of tasks"""
        self.print_header("Tasks List")
        self.print_status("🚧 Tasks feature coming soon...", "warning")
    
    def show_tasks_status(self):
        """Display tasks status overview"""
        self.print_header("Tasks Status Overview")
        self.print_status("🚧 Tasks feature coming soon...", "warning")
    
    def show_images_list(self):
        """Display list of images"""
        self.print_header("Images List")
        self.print_status("🚧 Images feature coming soon...", "warning")
    
    def show_config(self):
        """Show current configuration as key-value pairs"""
        self.print_header("SD-Host Configuration")
        
        # Configuration file info
        config_path = get_config_file_path()
        config_status = "exists" if config_path.exists() else "using defaults"
        print(f"{Colors.CYAN}Configuration File:{Colors.END} {config_path} ({config_status})")
        print()
        
        # Show all configuration values in key=value format
        config_items = [
            # App info
            ("app.name", self.settings.app_name),
            ("app.version", self.settings.app_version),
            
            # Storage
            ("storage.depot_dir", self.settings.depot_dir),
            ("storage.models_dir", self.settings.models_dir),
            ("storage.output_dir", self.settings.output_dir),
            ("storage.data_dir", self.settings.data_dir),
            ("storage.database_url", self.settings.database_url),
            ("storage.max_images", self.settings.storage.max_images),
            ("storage.cleanup_interval", self.settings.storage.cleanup_interval),
            ("storage.image_retention_days", self.settings.storage.image_retention_days),
            
            # Server
            ("server.host", self.settings.server.host),
            ("server.port", self.settings.server.port),
            ("server.debug", self.settings.server.debug),
            ("server.workers", self.settings.server.workers),
            ("server.reload", self.settings.server.reload),
            
            # Stable Diffusion
            ("stable_diffusion.model_name", self.settings.stable_diffusion.model_name),
            ("stable_diffusion.model_path", self.settings.stable_diffusion.model_path),
            ("stable_diffusion.device", self.settings.stable_diffusion.device),
            ("stable_diffusion.device_id", self.settings.stable_diffusion.device_id),
            ("stable_diffusion.precision", self.settings.stable_diffusion.precision),
            ("stable_diffusion.attention_slicing", self.settings.stable_diffusion.attention_slicing),
            ("stable_diffusion.memory_efficient_attention", self.settings.stable_diffusion.memory_efficient_attention),
            ("stable_diffusion.cpu_offload", self.settings.stable_diffusion.cpu_offload),
            ("stable_diffusion.default_width", self.settings.stable_diffusion.default_width),
            ("stable_diffusion.default_height", self.settings.stable_diffusion.default_height),
            ("stable_diffusion.default_steps", self.settings.stable_diffusion.default_steps),
            ("stable_diffusion.default_cfg_scale", self.settings.stable_diffusion.default_cfg_scale),
            ("stable_diffusion.default_sampler", self.settings.stable_diffusion.default_sampler),
            ("stable_diffusion.safety_checker", self.settings.stable_diffusion.safety_checker),
            ("stable_diffusion.nsfw_filter", self.settings.stable_diffusion.nsfw_filter),
            
            # API
            ("api.rate_limit_requests", self.settings.api.rate_limit_requests),
            ("api.rate_limit_window", self.settings.api.rate_limit_window),
            ("api.timeout", self.settings.api.timeout),
            ("api.max_request_size", self.settings.api.max_request_size),
            ("api.cors_origins", str(self.settings.api.cors_origins)),
            ("api.cors_methods", str(self.settings.api.cors_methods)),
            ("api.cors_headers", str(self.settings.api.cors_headers)),
            ("api.api_prefix", self.settings.api.api_prefix),
            
            # Civitai
            ("civitai.api_key", self.settings.civitai.api_key or "(not set)"),
            ("civitai.base_url", self.settings.civitai.base_url),
            
            # Proxy
            ("proxy.http_proxy", self.settings.proxy.http_proxy or "(not set)"),
            ("proxy.https_proxy", self.settings.proxy.https_proxy or "(not set)"),
            
            # Logging
            ("logging.level", self.settings.logging.level),
            ("logging.format", self.settings.logging.format),
            ("logging.file", self.settings.logging.file),
            ("logging.max_size", self.settings.logging.max_size),
            ("logging.backup_count", self.settings.logging.backup_count),
            
            # Security
            ("security.api_key_enabled", self.settings.security.api_key_enabled),
            ("security.api_key", self.settings.security.api_key or "(not set)"),
            ("security.ssl_enabled", self.settings.security.ssl_enabled),
            ("security.ssl_cert_file", self.settings.security.ssl_cert_file or "(not set)"),
            ("security.ssl_key_file", self.settings.security.ssl_key_file or "(not set)"),
            
            # Monitoring
            ("monitoring.health_check_enabled", self.settings.monitoring.health_check_enabled),
            ("monitoring.metrics_enabled", self.settings.monitoring.metrics_enabled),
            ("monitoring.metrics_endpoint", self.settings.monitoring.metrics_endpoint),
            ("monitoring.track_performance", self.settings.monitoring.track_performance),
            
            # File
            ("file.max_file_size", self.settings.file.max_file_size),
            ("file.allowed_extensions", str(self.settings.file.allowed_extensions)),
        ]
        
        # Calculate max key length for alignment
        max_key_length = max(len(key) for key, _ in config_items)
        
        # Print all configuration items
        for key, value in config_items:
            # Format the value
            if isinstance(value, bool):
                value_str = f"{Colors.GREEN}true{Colors.END}" if value else f"{Colors.RED}false{Colors.END}"
            elif isinstance(value, str) and value == "(not set)":
                value_str = f"{Colors.YELLOW}(not set){Colors.END}"
            elif isinstance(value, (int, float)):
                value_str = f"{Colors.BLUE}{value}{Colors.END}"
            else:
                value_str = str(value)
            
            # Print with alignment
            print(f"{Colors.CYAN}{key:<{max_key_length}}{Colors.END} = {value_str}")
        
        print()
        print(f"{Colors.YELLOW}💡 Tip:{Colors.END} Use 'sdh config set <key> <value>' to modify configuration values")
    
    def show_config_path(self):
        """Show configuration file path"""
        config_path = get_config_file_path()
        print(f"Configuration file: {config_path}")
        if config_path.exists():
            print(f"Status: {Colors.GREEN}exists{Colors.END}")
        else:
            print(f"Status: {Colors.YELLOW}not found (using defaults){Colors.END}")
    
    def init_config(self):
        """Initialize configuration file"""
        from core.config import save_config
        
        config_path = get_config_file_path()
        
        if config_path.exists():
            print(f"{Colors.YELLOW}Configuration file already exists at:{Colors.END}")
            print(f"  {config_path}")
            print()
            response = input("Overwrite existing configuration? [y/N]: ")
            if response.lower() not in ['y', 'yes']:
                print("Configuration initialization cancelled.")
                return
        
        try:
            # Create configuration with current settings
            save_config(self.settings)
            print(f"{Colors.GREEN}✅ Configuration file created successfully:{Colors.END}")
            print(f"  {config_path}")
            print()
            print(f"{Colors.CYAN}📁 Depot directory:{Colors.END} {self.settings.depot_dir}")
            print()
            print("You can now edit the configuration file to customize your settings.")
            
        except Exception as e:
            print(f"{Colors.RED}❌ Failed to create configuration file:{Colors.END}")
            print(f"  Error: {e}")
    
    def get_config_value(self, key: str):
        """Get a specific configuration value"""
        try:
            value = self._get_nested_value(key)
            if value is None:
                print(f"{Colors.RED}❌ Configuration key not found:{Colors.END} {key}")
                return
            
            # Format output
            if isinstance(value, bool):
                value_str = "true" if value else "false"
            elif isinstance(value, str) and not value:
                value_str = "(empty)"
            else:
                value_str = str(value)
            
            print(f"{Colors.CYAN}{key}{Colors.END} = {value_str}")
            
        except Exception as e:
            print(f"{Colors.RED}❌ Error getting configuration value:{Colors.END}")
            print(f"  Error: {e}")
    
    def set_config_value(self, key: str, value: str):
        """Set a specific configuration value"""
        try:
            # Parse the value to appropriate type
            parsed_value = self._parse_config_value(key, value)
            
            # Set the value in settings
            success = self._set_nested_value(key, parsed_value)
            
            if not success:
                print(f"{Colors.RED}❌ Invalid configuration key:{Colors.END} {key}")
                print(f"{Colors.YELLOW}💡 Tip:{Colors.END} Use 'sdh config show' to see available keys")
                return
            
            # Save configuration to file
            from core.config import save_config
            save_config(self.settings)
            
            print(f"{Colors.GREEN}✅ Configuration updated:{Colors.END}")
            print(f"  {Colors.CYAN}{key}{Colors.END} = {parsed_value}")
            print()
            print(f"{Colors.YELLOW}💡 Note:{Colors.END} Restart the service for changes to take effect")
            
        except ValueError as e:
            print(f"{Colors.RED}❌ Invalid value:{Colors.END} {e}")
        except Exception as e:
            print(f"{Colors.RED}❌ Error setting configuration value:{Colors.END}")
            print(f"  Error: {e}")
    
    def _get_nested_value(self, key: str):
        """Get nested configuration value using dot notation"""
        parts = key.split('.')
        current = self.settings
        
        for part in parts:
            if hasattr(current, part):
                current = getattr(current, part)
            else:
                return None
        
        return current
    
    def _set_nested_value(self, key: str, value) -> bool:
        """Set nested configuration value using dot notation"""
        parts = key.split('.')
        current = self.settings
        
        # Navigate to the parent object
        for part in parts[:-1]:
            if hasattr(current, part):
                current = getattr(current, part)
            else:
                return False
        
        # Set the final value
        final_key = parts[-1]
        if hasattr(current, final_key):
            setattr(current, final_key, value)
            # Recalculate paths if we modified storage settings
            if parts[0] == 'storage':
                self.settings._resolve_paths()
            return True
        
        return False
    
    def _parse_config_value(self, key: str, value: str):
        """Parse string value to appropriate type based on key"""
        # Get current value to determine type
        current_value = self._get_nested_value(key)
        
        if current_value is None:
            raise ValueError(f"Unknown configuration key: {key}")
        
        # Parse based on current value type
        if isinstance(current_value, bool):
            if value.lower() in ('true', '1', 'yes', 'on'):
                return True
            elif value.lower() in ('false', '0', 'no', 'off'):
                return False
            else:
                raise ValueError(f"Invalid boolean value: {value}. Use: true/false, 1/0, yes/no, on/off")
        
        elif isinstance(current_value, int):
            try:
                return int(value)
            except ValueError:
                raise ValueError(f"Invalid integer value: {value}")
        
        elif isinstance(current_value, float):
            try:
                return float(value)
            except ValueError:
                raise ValueError(f"Invalid float value: {value}")
        
        elif isinstance(current_value, list):
            # Parse list values (comma-separated)
            if value.startswith('[') and value.endswith(']'):
                # JSON-style list
                import json
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    raise ValueError(f"Invalid list format: {value}")
            else:
                # Comma-separated values
                return [item.strip() for item in value.split(',') if item.strip()]
        
        else:
            # String value
            return value
    
    def show_help(self):
        """Show detailed help information"""
        help_text = f"""
{Colors.BOLD}{Colors.CYAN}SD-Host CLI Tool (sdh){Colors.END}

{Colors.BOLD}DESCRIPTION:{Colors.END}
    Command-line interface for managing SD-Host service and querying status.
    
{Colors.BOLD}GLOBAL OPTIONS:{Colors.END}
    --depot, -d PATH     Specify depot directory (overrides SDH_DEPOT env var)
    --config, -c PATH    Specify configuration file path
    --version            Show version information
    --help               Show this help message

{Colors.BOLD}DEPOT MANAGEMENT:{Colors.END}
    The depot is the root directory where SD-Host stores all its data:
    - models/    Model files (.safetensors, .ckpt, etc.)
    - output/    Generated images and outputs
    - data/      Database and application data
    - logs/      Application logs
    
    Depot location priority:
    1. --depot command line argument
    2. SDH_DEPOT environment variable  
    3. Default: ~/sd-host/depot

{Colors.BOLD}CONFIGURATION:{Colors.END}
    Configuration file: ~/sd-host/config.yml
    
    sdh config init         - Create initial configuration file
    sdh config show         - Show all configuration as key-value pairs
    sdh config get <key>    - Get specific configuration value
    sdh config set <key> <value> - Set configuration value
    sdh config path         - Show configuration file path

{Colors.BOLD}SERVICE MANAGEMENT:{Colors.END}
    sdh service status   - Show service status and system info
    sdh service start    - Start SD-Host API service
    sdh service stop     - Stop SD-Host API service  
    sdh service restart  - Restart SD-Host API service

{Colors.BOLD}MODELS MANAGEMENT:{Colors.END}
    sdh models list      - List all available models
    sdh models status    - Show models overview and usage

{Colors.BOLD}IMAGES MANAGEMENT:{Colors.END}
    sdh images list      - List all images (coming soon)

{Colors.BOLD}TASKS MANAGEMENT:{Colors.END}
    sdh tasks list       - List all tasks (coming soon)
    sdh tasks status     - Show tasks overview (coming soon)

{Colors.BOLD}EXAMPLES:{Colors.END}
    # Use custom depot location
    sdh --depot /path/to/my/depot service start
    
    # Initialize configuration
    sdh config init
    
    # Check service status  
    sdh service status
    
    # List models with custom depot
    SDH_DEPOT=/custom/path sdh models list
    
    # Configuration management
    sdh config show                     # Show all settings
    sdh config get server.port          # Get specific value
    sdh config set server.port 9000     # Set new value
    sdh config set server.debug true    # Set boolean value
    sdh config set api.cors_origins "*,http://localhost:3000"  # Set list

{Colors.BOLD}ENVIRONMENT VARIABLES:{Colors.END}
    SDH_DEPOT            Depot directory path
        """
        print(help_text)
    
    def _colored_status(self, status: str) -> str:
        """Return colored status string"""
        colors = {
            "ready": Colors.GREEN,
            "downloading": Colors.YELLOW,
            "error": Colors.RED,
            "pending": Colors.BLUE
        }
        color = colors.get(status, Colors.WHITE)
        return f"{color}{status}{Colors.END}"

def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="SD-Host CLI Tool - Manage SD-Host service and query status",
        prog="sdh"
    )
    
    parser.add_argument("--version", action="version", version="sdh 1.0.0")
    parser.add_argument("--depot", "-d", type=str, help="Depot directory path (overrides SDH_DEPOT env var)")
    parser.add_argument("--config", "-c", type=str, help="Configuration file path")
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Service management
    service_parser = subparsers.add_parser("service", help="Service management")
    service_parser.add_argument("action", choices=["status", "start", "stop", "restart"], 
                               help="Service action")
    
    # Models management
    models_parser = subparsers.add_parser("models", help="Models management")
    models_parser.add_argument("action", choices=["list", "status"], 
                              help="Models action")
    
    # Images management
    images_parser = subparsers.add_parser("images", help="Images management")
    images_parser.add_argument("action", choices=["list"], 
                              help="Images action")
    
    # Tasks management
    tasks_parser = subparsers.add_parser("tasks", help="Tasks management")
    tasks_parser.add_argument("action", choices=["list", "status"], 
                             help="Tasks action")
    
    # Config management
    config_parser = subparsers.add_parser("config", help="Configuration management")
    config_subparsers = config_parser.add_subparsers(dest="config_action", help="Config actions")
    
    # Config show
    config_show_parser = config_subparsers.add_parser("show", help="Show all configuration values")
    
    # Config get
    config_get_parser = config_subparsers.add_parser("get", help="Get specific configuration value")
    config_get_parser.add_argument("key", help="Configuration key (e.g., server.port)")
    
    # Config set
    config_set_parser = config_subparsers.add_parser("set", help="Set configuration value")
    config_set_parser.add_argument("key", help="Configuration key (e.g., server.port)")
    config_set_parser.add_argument("value", help="Configuration value")
    
    # Config path
    config_path_parser = config_subparsers.add_parser("path", help="Show configuration file path")
    
    # Config init
    config_init_parser = config_subparsers.add_parser("init", help="Initialize configuration file")
    
    args = parser.parse_args()
    
    # If no command provided, show help
    if not args.command:
        parser.print_help()
        return
    
    cli = SDHostCLI(depot_dir=args.depot, config_path=args.config)
    
    # Handle commands
    if args.command == "service":
        if args.action == "status":
            cli.show_service_status()
        elif args.action == "start":
            cli.start_service()
        elif args.action == "stop":
            cli.stop_service()
        elif args.action == "restart":
            cli.restart_service()
    
    elif args.command == "models":
        if args.action == "list":
            cli.show_models_list()
        elif args.action == "status":
            cli.show_models_status()
    
    elif args.command == "images":
        if args.action == "list":
            cli.show_images_list()
    
    elif args.command == "tasks":
        if args.action == "list":
            cli.show_tasks_list()
        elif args.action == "status":
            cli.show_tasks_status()
    
    elif args.command == "config":
        if args.config_action == "show":
            cli.show_config()
        elif args.config_action == "get":
            cli.get_config_value(args.key)
        elif args.config_action == "set":
            cli.set_config_value(args.key, args.value)
        elif args.config_action == "path":
            cli.show_config_path()
        elif args.config_action == "init":
            cli.init_config()
        else:
            # If no subcommand, show help for config
            config_parser.print_help()

if __name__ == "__main__":
    main()
