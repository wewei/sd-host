"""
Service management commands
"""

import subprocess
import time
import os
from datetime import datetime
from typing import Optional

import typer
import psutil
import requests
from rich.table import Table

from ..utils import console, success, error, warning, info, header, format_bytes, CLIState

app = typer.Typer(help="Service management commands")

@app.command()
def status(
    ctx: typer.Context,
):
    """Show service status and system information"""
    cli_state = ctx.obj
    
    header("SD-Host Service Status")
    
    status_info = _get_service_status(cli_state)
    
    # Create status table
    table = Table(title="Service Information", show_header=True, header_style="bold cyan")
    table.add_column("Property", style="cyan", width=20)
    table.add_column("Value", style="white")
    
    if status_info["running"]:
        table.add_row("Status", "[green]🟢 RUNNING[/green]")
        table.add_row("PID", str(status_info["pid"]))
        table.add_row("Uptime", status_info["uptime"])
        table.add_row("Memory Usage", status_info["memory"])
        table.add_row("CPU Usage", status_info["cpu"])
        
        if status_info["api_accessible"]:
            table.add_row("API Status", "[green]🌐 Accessible[/green]")
        else:
            table.add_row("API Status", "[red]🚫 Not Accessible[/red]")
            
        table.add_row("API URL", f"http://{cli_state.settings.host}:{cli_state.settings.port}")
    else:
        table.add_row("Status", "[red]🔴 STOPPED[/red]")
        table.add_row("API URL", f"http://{cli_state.settings.host}:{cli_state.settings.port}")
    
    console.print(table)
    console.print()

@app.command()
def start(
    ctx: typer.Context,
):
    """Start the SD-Host service"""
    cli_state = ctx.obj
    
    if _is_service_running(cli_state):
        error("Service is already running")
        raise typer.Exit(1)
    
    if not cli_state.python_exe.exists():
        error("Python virtual environment not found")
        info(f"Expected: {cli_state.python_exe}")
        raise typer.Exit(1)
    
    if not cli_state.main_script.exists():
        error("Main script not found")
        info(f"Expected: {cli_state.main_script}")
        raise typer.Exit(1)
    
    with console.status("[bold blue]Starting SD-Host service..."):
        try:
            # Start process in background
            process = subprocess.Popen(
                [str(cli_state.python_exe), str(cli_state.main_script)],
                stdout=open(cli_state.log_file, 'w'),
                stderr=subprocess.STDOUT,
                cwd=str(cli_state.project_dir),
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
            )
            
            # Save PID
            with open(cli_state.pid_file, 'w') as f:
                f.write(str(process.pid))
            
            # Wait a moment and check if it started successfully
            time.sleep(3)
            
            if _is_service_running(cli_state):
                success(f"Service started successfully (PID: {process.pid})")
                info(f"API available at: http://{cli_state.settings.host}:{cli_state.settings.port}")
                info(f"Logs: {cli_state.log_file}")
            else:
                error("Service failed to start")
                info(f"Check logs: {cli_state.log_file}")
                raise typer.Exit(1)
                
        except Exception as e:
            error(f"Error starting service: {e}")
            raise typer.Exit(1)

@app.command()
def stop(
    ctx: typer.Context,
):
    """Stop the SD-Host service"""
    cli_state = ctx.obj
    
    pid = _is_service_running(cli_state)
    
    if not pid:
        error("Service is not running")
        raise typer.Exit(1)
    
    with console.status(f"[bold blue]Stopping SD-Host service (PID: {pid})..."):
        try:
            proc = psutil.Process(pid)
            proc.terminate()
            
            # Wait for graceful shutdown
            try:
                proc.wait(timeout=10)
            except psutil.TimeoutExpired:
                proc.kill()  # Force kill if graceful shutdown fails
            
            # Clean up PID file
            if cli_state.pid_file.exists():
                cli_state.pid_file.unlink()
            
            success("Service stopped successfully")
            
        except psutil.NoSuchProcess:
            error("Process not found")
            if cli_state.pid_file.exists():
                cli_state.pid_file.unlink()
            raise typer.Exit(1)
        except Exception as e:
            error(f"Error stopping service: {e}")
            raise typer.Exit(1)

@app.command()
def restart(
    ctx: typer.Context,
):
    """Restart the SD-Host service"""
    cli_state = ctx.obj
    
    info("Restarting SD-Host service...")
    
    if _is_service_running(cli_state):
        # Stop the service
        ctx.invoke(stop)
        time.sleep(2)
    
    # Start the service
    ctx.invoke(start)

@app.command()
def logs(
    ctx: typer.Context,
    follow: bool = typer.Option(False, "--follow", "-f", help="Follow log output"),
    lines: int = typer.Option(50, "--lines", "-n", help="Number of lines to show")
):
    """Show service logs"""
    cli_state = ctx.obj
    
    if not cli_state.log_file.exists():
        error(f"Log file not found: {cli_state.log_file}")
        raise typer.Exit(1)
    
    if follow:
        info(f"Following logs from: {cli_state.log_file}")
        info("Press Ctrl+C to stop")
        try:
            # Use tail -f equivalent for Windows
            if os.name == 'nt':
                subprocess.run([
                    "powershell", "-Command", 
                    f"Get-Content '{cli_state.log_file}' -Tail {lines} -Wait"
                ])
            else:
                subprocess.run(["tail", "-f", "-n", str(lines), str(cli_state.log_file)])
        except KeyboardInterrupt:
            info("Stopped following logs")
    else:
        # Show last N lines
        try:
            with open(cli_state.log_file, 'r', encoding='utf-8') as f:
                lines_list = f.readlines()
                for line in lines_list[-lines:]:
                    console.print(line.rstrip())
        except Exception as e:
            error(f"Error reading log file: {e}")
            raise typer.Exit(1)

def _is_service_running(cli_state: CLIState) -> Optional[int]:
    """Check if SD-Host service is running, return PID if found"""
    if not cli_state.pid_file.exists():
        return None
    
    try:
        with open(cli_state.pid_file, 'r') as f:
            pid = int(f.read().strip())
        
        # Check if process exists and is our python process
        if psutil.pid_exists(pid):
            return pid
        
        # PID file exists but process is not running, clean up
        cli_state.pid_file.unlink()
        return None
        
    except (ValueError, psutil.NoSuchProcess, PermissionError):
        return None

def _get_service_status(cli_state: CLIState) -> dict:
    """Get comprehensive service status"""
    pid = _is_service_running(cli_state)
    
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
            response = requests.get(f"{cli_state.api_base}/health", timeout=5)
            api_accessible = response.status_code == 200
        except:
            pass
        
        return {
            "running": True,
            "pid": pid,
            "uptime": str(uptime).split('.')[0],
            "memory": format_bytes(proc.memory_info().rss),
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
