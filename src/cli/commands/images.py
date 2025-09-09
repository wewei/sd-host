"""
Images management commands
"""

import typer

from ..utils import console, warning, info, header

app = typer.Typer(help="Images management commands")

@app.command()
def list(
    ctx: typer.Context,
    limit: int = typer.Option(10, "--limit", "-l", help="Number of images to show"),
):
    """List generated images (coming soon)"""
    header("Images List")
    warning("🚧 Images feature coming soon...")

@app.command()
def clean(
    ctx: typer.Context,
    days: int = typer.Option(7, "--days", "-d", help="Remove images older than N days"),
    force: bool = typer.Option(False, "--force", "-f", help="Force cleanup without confirmation")
):
    """Clean up old images (coming soon)"""
    warning("🚧 Image cleanup feature coming soon...")
    info(f"Would clean images older than {days} days")
