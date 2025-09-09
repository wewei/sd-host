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

# Add src to Python path for imports (CLI is in cli/ subdirectory)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

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
    
    def __init__(self):
        # CLI is in cli/ subdirectory, so project root is parent directory
        self.project_dir = Path(__file__).parent.parent.absolute()
        self.python_exe = self.project_dir / "venv" / "Scripts" / "python.exe"
        self.main_script = self.project_dir / "src" / "main.py"
        self.pid_file = self.project_dir / ".sdh.pid"
        self.log_file = self.project_dir / "logs" / "sdh.log"
        self.api_base = "http://localhost:8000"
        
        # Ensure logs directory exists
        self.log_file.parent.mkdir(exist_ok=True)
    
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
    
    def show_help(self):
        """Display help information"""
        self.print_header("SD-Host CLI (sdh) - Help")
        
        help_text = """
🔧 Service Management:
   sdh service status    - Show service status
   sdh service start     - Start the service
   sdh service stop      - Stop the service
   sdh service restart   - Restart the service

📦 Models Management:
   sdh models list       - List all models
   sdh models status     - Show models overview

🖼️  Images Management:
   sdh images list       - List all images (coming soon)

⚙️  Tasks Management:
   sdh tasks list        - List all tasks (coming soon)
   sdh tasks status      - Show tasks overview (coming soon)

📝 General:
   sdh --help           - Show this help
   sdh --version        - Show version information

🌐 Web Interface:
   Access the web API at: http://localhost:8000
   API Documentation: http://localhost:8000/docs
        """
        print(help_text)

def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="SD-Host CLI Tool - Manage SD-Host service and query status",
        prog="sdh"
    )
    
    parser.add_argument("--version", action="version", version="sdh 1.0.0")
    
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
    
    args = parser.parse_args()
    
    # If no command provided, show help
    if not args.command:
        parser.print_help()
        return
    
    cli = SDHostCLI()
    
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

if __name__ == "__main__":
    main()
