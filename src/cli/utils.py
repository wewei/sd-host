"""
CLI utilities and common functions
"""

from pathlib import Path
from typing import Optional
import os
import sys

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box

# Add src to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from core.config import load_config, get_config_file_path

# Global console instance
console = Console()

class CLIState:
    """Shared CLI state and utilities"""
    
    def __init__(self, depot_dir: Optional[str] = None, config_path: Optional[str] = None):
        # CLI is in src/cli/ subdirectory, so project root is two levels up
        self.project_dir = Path(__file__).parent.parent.parent.absolute()
        self.python_exe = self.project_dir / "venv" / "Scripts" / "python.exe"
        self.main_script = self.project_dir / "src" / "api" / "main.py"
        
        # Load configuration with depot override
        self.settings = load_config(config_path, depot_dir)
        
        # Set up paths based on configuration
        self.pid_file = Path(self.settings.depot_dir) / ".sdh.pid"
        self.log_file = Path(self.settings.logging.file)
        # Use localhost for CLI connections if host is 0.0.0.0
        host = self.settings.host if self.settings.host != "0.0.0.0" else "localhost"
        self.api_base = f"http://{host}:{self.settings.port}"
        
        # Ensure directories exist
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        Path(self.settings.depot_dir).mkdir(parents=True, exist_ok=True)

def success(message: str):
    """Print success message"""
    console.print(f"✅ {message}", style="green")

def error(message: str):
    """Print error message"""
    console.print(f"❌ {message}", style="red")

def warning(message: str):
    """Print warning message"""
    console.print(f"⚠️  {message}", style="yellow")

def info(message: str):
    """Print info message"""
    console.print(f"ℹ️  {message}", style="blue")

def header(text: str):
    """Print styled header"""
    console.print(Panel(Text(text, style="bold cyan"), box=box.DOUBLE))

def create_table(title: str) -> Table:
    """Create a styled table"""
    table = Table(title=title, box=box.ROUNDED, show_header=True, header_style="bold cyan")
    return table

def format_bytes(bytes_value: int) -> str:
    """Format bytes to human readable string"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.1f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.1f} PB"

def format_boolean(value: bool) -> str:
    """Format boolean with color"""
    if value:
        return "[green]true[/green]"
    else:
        return "[red]false[/red]"

def format_optional(value: Optional[str]) -> str:
    """Format optional string value"""
    if value:
        return value
    else:
        return "[yellow](not set)[/yellow]"
