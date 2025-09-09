#!/usr/bin/env python3
"""
SD-Host CLI Tool (sdh) - Modern implementation with Typer
Command-line interface for managing SD-Host service
"""

from typing import Optional
import sys
import os
from pathlib import Path

# Add src to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import typer
from rich import print
from rich.panel import Panel

from cli.utils import CLIState
from cli.commands import config, service, models, images, tasks

# Create main app
app = typer.Typer(
    name="sdh",
    help="[bold blue]SD-Host CLI Tool[/bold blue] - Manage SD-Host service and query status",
    epilog="Visit https://github.com/wewei/sd-host for more information.",
    rich_markup_mode="rich",
    no_args_is_help=True
)

# Add subcommands
app.add_typer(service.app, name="service", help="🔧 Service management")
app.add_typer(models.app, name="models", help="📦 Models management") 
app.add_typer(images.app, name="images", help="🖼️  Images management")
app.add_typer(tasks.app, name="tasks", help="⚙️  Tasks management")
app.add_typer(config.app, name="config", help="📝 Configuration management")

@app.command(name="version")
def version_command():
    """Show version information"""
    print("[bold blue]SD-Host CLI[/bold blue] version [green]1.0.0[/green]")

@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    depot: Optional[str] = typer.Option(
        None, 
        "--depot", "-d",
        help="Depot directory path (overrides SDH_DEPOT env var)",
        envvar="SDH_DEPOT"
    ),
    config_path: Optional[str] = typer.Option(
        None,
        "--config", "-c", 
        help="Configuration file path"
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose", "-v",
        help="Enable verbose output"
    ),
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        help="Show version information"
    )
):
    """
    SD-Host CLI Tool - Command-line interface for managing SD-Host service.
    
    The depot is the root directory where SD-Host stores all its data:
    models, output, database, and logs.
    
    Depot location priority:
    1. --depot command line argument
    2. SDH_DEPOT environment variable  
    3. Default: ~/sd-host/depot
    """
    if version:
        print("[bold blue]SD-Host CLI[/bold blue] version [green]1.0.0[/green]")
        raise typer.Exit()
    
    # Initialize CLI state and pass to all subcommands
    if ctx.invoked_subcommand is not None:
        ctx.obj = CLIState(depot_dir=depot, config_path=config_path)
        
        if verbose:
            print(f"[dim]Using depot: {ctx.obj.settings.depot_dir}[/dim]")
            print(f"[dim]Config loaded from: {config_path or 'default'}[/dim]")

@app.command(name="info")
def show_info(ctx: typer.Context):
    """Show system information and configuration summary"""
    cli_state = ctx.obj
    
    config_path = None
    try:
        from core.config import get_config_file_path
        config_path = get_config_file_path()
        config_status = "exists" if config_path.exists() else "not found"
    except:
        config_status = "not found"
    
    info_panel = Panel(
        f"""[bold cyan]SD-Host System Information[/bold cyan]

[yellow]Configuration:[/yellow]
• Config File: [blue]{config_path}[/blue] ({config_status})
• Depot Directory: [green]{cli_state.settings.depot_dir}[/green]
• Models Directory: {cli_state.settings.models_dir}
• Output Directory: {cli_state.settings.output_dir}
• Database: {cli_state.settings.database_url}

[yellow]Server:[/yellow]
• Host: [blue]{cli_state.settings.server.host}[/blue]
• Port: [blue]{cli_state.settings.server.port}[/blue]
• Debug Mode: {'[green]enabled[/green]' if cli_state.settings.server.debug else '[red]disabled[/red]'}

[yellow]Quick Commands:[/yellow]
• [cyan]sdh service status[/cyan] - Check service status
• [cyan]sdh service start[/cyan] - Start the service
• [cyan]sdh models list[/cyan] - List available models
• [cyan]sdh config show[/cyan] - Show all configuration
""",
        title="ℹ️  System Info",
        border_style="blue"
    )
    
    print(info_panel)

if __name__ == "__main__":
    app()
