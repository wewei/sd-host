"""
Models management commands
"""

import re
from typing import Optional, Dict, Any
import asyncio
import time

import typer
import requests
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeRemainingColumn
from rich.live import Live
from rich.panel import Panel

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


def _parse_civitai_url(url: str) -> Optional[Dict[str, str]]:
    """Parse CivitAI URL to extract model ID and version ID"""
    # Pattern for CivitAI URLs: https://civitai.com/models/{model_id}/{name}?modelVersionId={version_id}
    pattern = r'https://civitai\.com/models/(\d+)(?:/[^?]*)?(?:\?.*modelVersionId=(\d+))?'
    match = re.match(pattern, url)
    
    if match:
        model_id = match.group(1)
        version_id = match.group(2)
        return {
            "model_id": model_id,
            "version_id": version_id
        }
    return None


def _api_post_request(cli_state: CLIState, endpoint: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Make a POST request to the API"""
    from .service import _is_service_running
    
    if not _is_service_running(cli_state):
        error("Service is not running")
        info("Start the service with: sdh service start")
        return None
    
    try:
        response = requests.post(f"{cli_state.api_base}{endpoint}", json=data, timeout=30)
        if response.status_code in [200, 201, 202]:
            return response.json()
        else:
            error(f"API request failed: {response.status_code}")
            if response.text:
                error(f"Response: {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        error(f"Connection error: {e}")
        return None


def _track_download_progress(cli_state: CLIState, tracking_hash: str, show_details: bool = True):
    """Track download progress using SSE"""
    try:
        import sseclient
    except ImportError:
        error("sseclient-py is required for progress tracking")
        info("Install with: pip install sseclient-py")
        return False
    
    try:
        url = f"{cli_state.api_base}/api/models/add-from-civitai/{tracking_hash}"
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeRemainingColumn(),
            console=console,
            transient=False,
        ) as progress:
            
            download_task = progress.add_task("Downloading model...", total=100)
            
            try:
                response = requests.get(url, stream=True, timeout=10)
                client = sseclient.SSEClient(response)
                
                for event in client.events():
                    if event.data:
                        try:
                            import json
                            # Try to parse as JSON first
                            parsed_data = json.loads(event.data)
                            
                            # Check if it's already a dictionary (direct JSON object)
                            if isinstance(parsed_data, dict):
                                data = parsed_data
                            # If it's a string containing SSE format "data: {JSON}\n\n"
                            elif isinstance(parsed_data, str) and parsed_data.startswith("data: "):
                                json_part = parsed_data[6:].rstrip('\n')  # Remove "data: " prefix and trailing newlines
                                data = json.loads(json_part)
                            else:
                                continue
                            
                            status = data.get("status", "unknown")
                            
                            if status == "downloading":
                                progress_value = data.get("progress", 0)
                                speed = data.get("speed", "0 B/s")
                                eta = data.get("eta", "calculating...")
                                
                                progress.update(download_task, 
                                              completed=progress_value,
                                              description=f"Downloading... {speed} | ETA: {eta}")
                                
                            elif status == "completed":
                                progress.update(download_task, completed=100)
                                model_info = data.get("model_info")
                                if model_info and show_details:
                                    success(f"✅ Download completed!")
                                    info(f"Model: {model_info.get('name', 'Unknown')}")
                                    info(f"Hash: {model_info.get('hash', 'Unknown')}")
                                    info(f"Size: {format_bytes(model_info.get('size', 0))}")
                                else:
                                    success("✅ Download completed!")
                                return True
                                
                            elif status == "failed":
                                error_msg = data.get("error", "Unknown error")
                                error(f"❌ Download failed: {error_msg}")
                                return False
                                
                        except json.JSONDecodeError:
                            continue
                            
            except requests.exceptions.RequestException as e:
                error(f"Failed to connect to progress stream: {e}")
                return False
                
    except Exception as e:
        error(f"Progress tracking failed: {e}")
        return False
    
    return False


@app.command("add-from-civitai")
def add_from_civitai(
    ctx: typer.Context,
    url_or_model_id: Optional[str] = typer.Argument(None, help="CivitAI URL or model ID"),
    version_id: Optional[str] = typer.Option(None, "--version-id", "-v", help="Model version ID (required if using model ID)"),
    background: bool = typer.Option(False, "--background", "-b", help="Download in background and return model hash"),
    tracking: Optional[str] = typer.Option(None, "--tracking", "-t", help="Track progress of existing download by hash"),
):
    """Add a model from CivitAI by URL or model/version ID"""
    cli_state = ctx.obj
    
    # Handle tracking mode
    if tracking:
        header(f"Tracking Download Progress")
        info(f"Tracking hash: {tracking}")
        success_result = _track_download_progress(cli_state, tracking, show_details=True)
        if success_result:
            success("Download tracking completed")
        else:
            error("Download tracking failed or was interrupted")
        return
    
    # For non-tracking mode, URL or model ID is required
    if not url_or_model_id:
        error("URL or model ID is required when not in tracking mode")
        info("Use: sdh models add-from-civitai <url_or_model_id> [options]")
        info("Or: sdh models add-from-civitai --tracking <hash>")
        return
    
    # Parse input
    model_id = None
    version_id_to_use = version_id
    
    if url_or_model_id.startswith("http"):
        # Parse URL
        parsed = _parse_civitai_url(url_or_model_id)
        if not parsed:
            error("Invalid CivitAI URL format")
            info("Expected format: https://civitai.com/models/{model_id}/...?modelVersionId={version_id}")
            return
        
        model_id = parsed["model_id"]
        if parsed["version_id"]:
            version_id_to_use = parsed["version_id"]
            
    else:
        # Assume it's a model ID
        model_id = url_or_model_id
    
    if not model_id:
        error("Model ID is required")
        return
    
    if not version_id_to_use:
        error("Version ID is required")
        info("Provide it via --version-id option or use a URL with modelVersionId parameter")
        return
    
    header(f"Adding Model from CivitAI")
    info(f"Model ID: {model_id}")
    info(f"Version ID: {version_id_to_use}")
    
    # Start download
    data = {
        "model_id": model_id,
        "version_id": version_id_to_use
    }
    
    response = _api_post_request(cli_state, "/api/models/add-from-civitai", data)
    if not response:
        return
    
    tracking_hash = response.get("hash")
    if not tracking_hash:
        error("Failed to get tracking hash from response")
        return
    
    if background:
        # Background mode - just return the hash
        success("✅ Download started in background")
        info(f"Model hash: {tracking_hash}")
        info(f"Track progress with: sdh models add-from-civitai --tracking {tracking_hash}")
    else:
        # Foreground mode - track progress
        info(f"Tracking hash: {tracking_hash}")
        info("Tracking download progress...")
        
        success_result = _track_download_progress(cli_state, tracking_hash, show_details=True)
        if success_result:
            success("🎉 Model successfully added!")
        else:
            error("Download was interrupted or failed")
            info(f"You can resume tracking with: sdh models add-from-civitai --tracking {tracking_hash}")


# ==================== Download Task Management Commands ====================

@app.command("download-tasks")
def list_download_tasks(
    ctx: typer.Context,
    status_filter: Optional[str] = typer.Option(None, "--status", "-s", help="Filter by status (downloading, paused, completed, failed, cancelled)"),
):
    """List all download tasks with their current status"""
    cli_state = ctx.obj
    
    header("Download Tasks")
    
    data = _api_request(cli_state, "/api/models/download-tasks")
    if not data:
        return
    
    tasks = data.get("data", [])
    
    if not tasks:
        info("📭 No download tasks found")
        return
    
    # Filter by status if specified
    if status_filter:
        tasks = [t for t in tasks if t.get("status") == status_filter]
    
    if not tasks:
        info(f"📭 No download tasks found with status '{status_filter}'")
        return
    
    # Create tasks table
    table = Table(title=f"Download Tasks ({len(tasks)})", show_header=True, header_style="bold cyan")
    table.add_column("Model", style="white", width=30)
    table.add_column("Status", style="yellow", width=12)
    table.add_column("Progress", style="green", width=10)
    table.add_column("Speed", style="blue", width=12)
    table.add_column("ETA", style="magenta", width=10)
    table.add_column("Hash", style="dim", width=16)
    
    for task in tasks:
        # Format status with colors
        status = task.get("status", "unknown")
        status_colored = {
            "downloading": "[green]downloading[/green]",
            "paused": "[yellow]paused[/yellow]",
            "completed": "[blue]completed[/blue]",
            "failed": "[red]failed[/red]",
            "cancelled": "[dim]cancelled[/dim]",
        }.get(status, status)
        
        # Format progress
        progress = task.get("progress", 0.0)
        progress_str = f"{progress:.1f}%"
        
        # Format size info
        model_name = task.get("model_name", "Unknown")
        version_name = task.get("version_name", "")
        if version_name:
            display_name = f"{model_name}\n[dim]{version_name}[/dim]"
        else:
            display_name = model_name
        
        table.add_row(
            display_name,
            status_colored,
            progress_str,
            task.get("speed", "0 B/s"),
            task.get("eta", "N/A"),
            task.get("hash", "")[:16] + "..."
        )
    
    console.print(table)
    console.print()


@app.command("download-task")
def show_download_task(
    ctx: typer.Context,
    task_hash: str = typer.Argument(..., help="Download task hash"),
):
    """Show detailed information for a specific download task"""
    cli_state = ctx.obj
    
    header(f"Download Task Details")
    
    data = _api_request(cli_state, f"/api/models/download-tasks/{task_hash}")
    if not data:
        return
    
    task = data.get("data")
    if not task:
        error("Download task not found")
        return
    
    # Create details table
    table = Table(title=f"Task: {task.get('hash', '')[:16]}...", show_header=True, header_style="bold cyan")
    table.add_column("Property", style="cyan", width=20)
    table.add_column("Value", style="white")
    
    # Format status with color
    status = task.get("status", "unknown")
    status_colored = {
        "downloading": "[green]downloading[/green]",
        "paused": "[yellow]paused[/yellow]",
        "completed": "[blue]completed[/blue]",
        "failed": "[red]failed[/red]",
        "cancelled": "[dim]cancelled[/dim]",
    }.get(status, status)
    
    table.add_row("Model Name", task.get("model_name", "Unknown"))
    table.add_row("Version Name", task.get("version_name", "Unknown"))
    table.add_row("Status", status_colored)
    table.add_row("Progress", f"{task.get('progress', 0.0):.1f}%")
    table.add_row("Speed", task.get("speed", "0 B/s"))
    table.add_row("ETA", task.get("eta", "N/A"))
    table.add_row("Size", format_bytes(task.get("size", 0)))
    table.add_row("Downloaded", format_bytes(task.get("downloaded", 0)))
    table.add_row("Created", task.get("created_at", "N/A"))
    table.add_row("Hash", task.get("hash", ""))
    
    if task.get("error"):
        table.add_row("Error", f"[red]{task.get('error')}[/red]")
    
    console.print(table)
    console.print()


@app.command("pause-download")
def pause_download_task(
    ctx: typer.Context,
    task_hash: str = typer.Argument(..., help="Download task hash to pause"),
):
    """Pause a download task"""
    cli_state = ctx.obj
    
    header(f"Pausing Download Task")
    
    data = {
        "action": "pause"
    }
    
    response = _api_post_request(cli_state, f"/api/models/download-tasks/{task_hash}/action", data)
    if not response:
        return
    
    if response.get("success"):
        success(f"✅ {response.get('message', 'Download paused')}")
    else:
        error(f"❌ {response.get('message', 'Failed to pause download')}")


@app.command("resume-download")
def resume_download_task(
    ctx: typer.Context,
    task_hash: str = typer.Argument(..., help="Download task hash to resume"),
):
    """Resume a paused download task"""
    cli_state = ctx.obj
    
    header(f"Resuming Download Task")
    
    data = {
        "action": "resume"
    }
    
    response = _api_post_request(cli_state, f"/api/models/download-tasks/{task_hash}/action", data)
    if not response:
        return
    
    if response.get("success"):
        success(f"✅ {response.get('message', 'Download resumed')}")
    else:
        error(f"❌ {response.get('message', 'Failed to resume download')}")


@app.command("cancel-download")
def cancel_download_task(
    ctx: typer.Context,
    task_hash: str = typer.Argument(..., help="Download task hash to cancel"),
    force: bool = typer.Option(False, "--force", "-f", help="Force cancellation without confirmation"),
):
    """Cancel a download task"""
    cli_state = ctx.obj
    
    header(f"Cancelling Download Task")
    
    if not force:
        confirm = typer.confirm("Are you sure you want to cancel this download? This will remove the partial file.")
        if not confirm:
            info("Cancellation aborted")
            return
    
    data = {
        "action": "cancel"
    }
    
    response = _api_post_request(cli_state, f"/api/models/download-tasks/{task_hash}/action", data)
    if not response:
        return
    
    if response.get("success"):
        success(f"✅ {response.get('message', 'Download cancelled')}")
    else:
        error(f"❌ {response.get('message', 'Failed to cancel download')}")


@app.command("remove-task")
def remove_download_task(
    ctx: typer.Context,
    task_hash: str = typer.Argument(..., help="Download task hash to remove"),
):
    """Remove a completed, failed, or cancelled download task"""
    cli_state = ctx.obj
    
    header(f"Removing Download Task")
    
    data = {
        "action": "remove"
    }
    
    response = _api_post_request(cli_state, f"/api/models/download-tasks/{task_hash}/action", data)
    if not response:
        return
    
    if response.get("success"):
        success(f"✅ {response.get('message', 'Task removed')}")
    else:
        error(f"❌ {response.get('message', 'Failed to remove task')}")


@app.command("clear-completed")
def clear_completed_tasks(
    ctx: typer.Context,
    force: bool = typer.Option(False, "--force", "-f", help="Force clear without confirmation"),
):
    """Remove all completed, failed, and cancelled download tasks"""
    cli_state = ctx.obj
    
    header(f"Clearing Completed Tasks")
    
    if not force:
        confirm = typer.confirm("Are you sure you want to remove all completed/failed/cancelled tasks?")
        if not confirm:
            info("Operation aborted")
            return
    
    response = _api_delete_request(cli_state, "/api/models/download-tasks/completed")
    if not response:
        return
    
    if response.get("success"):
        count = response.get("count", 0)
        success(f"✅ Removed {count} completed tasks")
    else:
        error(f"❌ {response.get('message', 'Failed to clear completed tasks')}")


def _api_delete_request(cli_state: CLIState, endpoint: str) -> Optional[Dict[str, Any]]:
    """Make a DELETE request to the API"""
    from .service import _is_service_running
    
    if not _is_service_running(cli_state):
        error("Service is not running")
        info("Start the service with: sdh service start")
        return None
    
    try:
        response = requests.delete(f"{cli_state.api_base}{endpoint}", timeout=30)
        if response.status_code in [200, 202, 204]:
            return response.json() if response.text else {"success": True}
        else:
            error(f"API request failed: {response.status_code}")
            if response.text:
                error(f"Response: {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        error(f"Connection error: {e}")
        return None
