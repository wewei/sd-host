"""
Models management commands
"""

from typing import Optional, Dict, Any
import asyncio

import typer
import requests
from rich.table import Table
from rich.progress import Progress

from ..utils import console, success, error, warning, info, header, format_bytes, CLIState

app = typer.Typer(help="Models management commands")

@app.command()
def list(
    ctx: typer.Context,
    limit: int = typer.Option(10, "--limit", "-l", help="Number of models to show"),
    model_type: Optional[str] = typer.Option(None, "--type", "-t", help="Filter by model type"),
):
    """List all available models"""
    cli_state = ctx.obj
    
    header("Models List")
    
    data = _api_request(cli_state, "/api/models")
    if not data:
        return
    
    models = data.get("data", [])
    
    if not models:
        info("📭 No models found")
        return
    
    # Filter by type if specified
    if model_type:
        models = [m for m in models if m.get("attributes", {}).get("model_type") == model_type]
    
    # Limit results
    models = models[:limit]
    
    # Create models table
    table = Table(title=f"Models ({len(models)} of {len(data.get('data', []))})", 
                  show_header=True, header_style="bold cyan")
    table.add_column("Name", style="white", width=30)
    table.add_column("Type", style="blue", width=12)
    table.add_column("Size", style="green", width=10)
    table.add_column("Status", style="yellow", width=12)
    table.add_column("Hash", style="dim", width=16)
    
    for model in models:
        attrs = model.get("attributes", {})
        name = attrs.get("name", "Unknown")
        model_type_val = attrs.get("model_type", "unknown")
        size = attrs.get("size", 0)
        status = attrs.get("status", "unknown")
        model_hash = model.get("id", "")[:16] + "..."
        
        # Format status with color
        if status == "ready":
            status_fmt = "[green]ready[/green]"
        elif status == "downloading":
            status_fmt = "[yellow]downloading[/yellow]"
        elif status == "error":
            status_fmt = "[red]error[/red]"
        else:
            status_fmt = status
        
        table.add_row(
            name,
            model_type_val,
            format_bytes(size),
            status_fmt,
            model_hash
        )
    
    console.print(table)
    console.print()
    
    if len(data.get("data", [])) > limit:
        info(f"Showing {limit} of {len(data.get('data', []))} models. Use --limit to show more.")

@app.command()
def status(
    ctx: typer.Context,
):
    """Show models status overview"""
    cli_state = ctx.obj
    
    header("Models Status Overview")
    
    data = _api_request(cli_state, "/api/models")
    if not data:
        return
    
    models = data.get("data", [])
    total = len(models)
    
    if total == 0:
        info("📭 No models found")
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
    
    # Create overview table
    table = Table(title="Models Overview", show_header=True, header_style="bold cyan")
    table.add_column("Metric", style="cyan", width=20)
    table.add_column("Value", style="white")
    
    table.add_row("Total Models", str(total))
    table.add_row("Total Size", format_bytes(total_size))
    table.add_row("", "")  # Separator
    
    # Add status breakdown
    for status, count in status_counts.items():
        if status == "ready":
            status_fmt = f"[green]{count}[/green]"
        elif status == "downloading":
            status_fmt = f"[yellow]{count}[/yellow]"
        elif status == "error":
            status_fmt = f"[red]{count}[/red]"
        else:
            status_fmt = str(count)
        table.add_row(f"Status: {status}", status_fmt)
    
    table.add_row("", "")  # Separator
    
    # Add type breakdown
    for model_type, count in type_counts.items():
        table.add_row(f"Type: {model_type}", str(count))
    
    console.print(table)
    console.print()

@app.command()
def download(
    url: str = typer.Argument(..., help="Civitai model URL"),
    ctx: typer.Context = None
):
    """Download a model from Civitai (coming soon)"""
    if ctx is None:
        ctx = typer.Context(download)
    warning("🚧 Model download feature coming soon...")
    info(f"URL: {url}")

@app.command() 
def remove(
    model_hash: str = typer.Argument(..., help="Model hash to remove"),
    ctx: typer.Context = None,
    force: bool = typer.Option(False, "--force", "-f", help="Force removal without confirmation")
):
    """Remove a model (coming soon)"""
    if ctx is None:
        ctx = typer.Context(remove)
    warning("🚧 Model removal feature coming soon...")
    info(f"Model hash: {model_hash}")

def _api_request(cli_state: CLIState, endpoint: str) -> Optional[Dict[str, Any]]:
    """Make API request to SD-Host service"""
    from .service import _is_service_running
    
    if not _is_service_running(cli_state):
        error("Service is not running")
        info("Start the service with: sdh service start")
        return None
    
    try:
        response = requests.get(f"{cli_state.api_base}{endpoint}", timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            error(f"API request failed: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        error(f"Connection error: {e}")
        return None
