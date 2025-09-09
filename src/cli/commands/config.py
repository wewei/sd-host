"""
Configuration management commands
"""

from pathlib import Path
from typing import Optional
import json

import typer
from rich.table import Table

from ..utils import console, success, error, warning, info, header, format_boolean, format_optional, CLIState
from core.config import get_config_file_path, save_config, reload_settings

app = typer.Typer(help="Configuration management commands")

@app.command()
def show(
    ctx: typer.Context,
):
    """Show all configuration values in key-value format"""
    cli_state = ctx.obj
    
    header("SD-Host Configuration")
    
    # Configuration file info
    config_path = get_config_file_path()
    config_status = "exists" if config_path.exists() else "using defaults"
    console.print(f"[cyan]Configuration File:[/cyan] {config_path} ({config_status})")
    console.print()
    
    # Create configuration table
    table = Table(title="Configuration Values", show_header=True, header_style="bold cyan")
    table.add_column("Key", style="cyan", width=40)
    table.add_column("Value", style="white")
    
    # Collect all configuration items
    config_items = [
        # App info
        ("app.name", cli_state.settings.app_name),
        ("app.version", cli_state.settings.app_version),
        
        # Storage
        ("storage.depot_dir", cli_state.settings.depot_dir),
        ("storage.models_dir", cli_state.settings.models_dir),
        ("storage.output_dir", cli_state.settings.output_dir),
        ("storage.data_dir", cli_state.settings.data_dir),
        ("storage.database_url", cli_state.settings.database_url),
        ("storage.max_images", str(cli_state.settings.storage.max_images)),
        ("storage.cleanup_interval", str(cli_state.settings.storage.cleanup_interval)),
        ("storage.image_retention_days", str(cli_state.settings.storage.image_retention_days)),
        
        # Server
        ("server.host", cli_state.settings.server.host),
        ("server.port", str(cli_state.settings.server.port)),
        ("server.debug", format_boolean(cli_state.settings.server.debug)),
        ("server.workers", str(cli_state.settings.server.workers)),
        ("server.reload", format_boolean(cli_state.settings.server.reload)),
        
        # Stable Diffusion
        ("stable_diffusion.model_name", cli_state.settings.stable_diffusion.model_name),
        ("stable_diffusion.model_path", cli_state.settings.stable_diffusion.model_path or "(auto)"),
        ("stable_diffusion.device", cli_state.settings.stable_diffusion.device),
        ("stable_diffusion.device_id", str(cli_state.settings.stable_diffusion.device_id)),
        ("stable_diffusion.precision", cli_state.settings.stable_diffusion.precision),
        ("stable_diffusion.attention_slicing", format_boolean(cli_state.settings.stable_diffusion.attention_slicing)),
        ("stable_diffusion.memory_efficient_attention", format_boolean(cli_state.settings.stable_diffusion.memory_efficient_attention)),
        ("stable_diffusion.cpu_offload", format_boolean(cli_state.settings.stable_diffusion.cpu_offload)),
        ("stable_diffusion.default_width", str(cli_state.settings.stable_diffusion.default_width)),
        ("stable_diffusion.default_height", str(cli_state.settings.stable_diffusion.default_height)),
        ("stable_diffusion.default_steps", str(cli_state.settings.stable_diffusion.default_steps)),
        ("stable_diffusion.default_cfg_scale", str(cli_state.settings.stable_diffusion.default_cfg_scale)),
        ("stable_diffusion.default_sampler", cli_state.settings.stable_diffusion.default_sampler),
        ("stable_diffusion.safety_checker", format_boolean(cli_state.settings.stable_diffusion.safety_checker)),
        ("stable_diffusion.nsfw_filter", format_boolean(cli_state.settings.stable_diffusion.nsfw_filter)),
        
        # API
        ("api.rate_limit_requests", str(cli_state.settings.api.rate_limit_requests)),
        ("api.rate_limit_window", str(cli_state.settings.api.rate_limit_window)),
        ("api.timeout", str(cli_state.settings.api.timeout)),
        ("api.max_request_size", str(cli_state.settings.api.max_request_size)),
        ("api.cors_origins", str(cli_state.settings.api.cors_origins)),
        ("api.cors_methods", str(cli_state.settings.api.cors_methods)),
        ("api.cors_headers", str(cli_state.settings.api.cors_headers)),
        ("api.api_prefix", cli_state.settings.api.api_prefix),
        
        # Civitai
        ("civitai.api_key", format_optional(cli_state.settings.civitai.api_key)),
        ("civitai.base_url", cli_state.settings.civitai.base_url),
        
        # Proxy
        ("proxy.http_proxy", format_optional(cli_state.settings.proxy.http_proxy)),
        ("proxy.https_proxy", format_optional(cli_state.settings.proxy.https_proxy)),
        
        # Logging
        ("logging.level", cli_state.settings.logging.level),
        ("logging.format", cli_state.settings.logging.format),
        ("logging.file", cli_state.settings.logging.file),
        ("logging.max_size", str(cli_state.settings.logging.max_size)),
        ("logging.backup_count", str(cli_state.settings.logging.backup_count)),
        
        # Security
        ("security.api_key_enabled", format_boolean(cli_state.settings.security.api_key_enabled)),
        ("security.api_key", format_optional(cli_state.settings.security.api_key)),
        ("security.ssl_enabled", format_boolean(cli_state.settings.security.ssl_enabled)),
        ("security.ssl_cert_file", format_optional(cli_state.settings.security.ssl_cert_file)),
        ("security.ssl_key_file", format_optional(cli_state.settings.security.ssl_key_file)),
        
        # Monitoring
        ("monitoring.health_check_enabled", format_boolean(cli_state.settings.monitoring.health_check_enabled)),
        ("monitoring.metrics_enabled", format_boolean(cli_state.settings.monitoring.metrics_enabled)),
        ("monitoring.metrics_endpoint", cli_state.settings.monitoring.metrics_endpoint),
        ("monitoring.track_performance", format_boolean(cli_state.settings.monitoring.track_performance)),
        
        # File
        ("file.max_file_size", str(cli_state.settings.file.max_file_size)),
        ("file.allowed_extensions", str(cli_state.settings.file.allowed_extensions)),
    ]
    
    # Add rows to table
    for key, value in config_items:
        table.add_row(key, value)
    
    console.print(table)
    console.print()
    info("Use 'sdh config set <key> <value>' to modify configuration values")

@app.command()
def get(
    key: str = typer.Argument(..., help="Configuration key (e.g., server.port)"),
    ctx: typer.Context = None
):
    """Get a specific configuration value"""
    if ctx is None:
        ctx = typer.Context(get)
    cli_state = ctx.obj
    
    try:
        value = _get_nested_value(cli_state.settings, key)
        if value is None:
            error(f"Configuration key not found: {key}")
            raise typer.Exit(1)
        
        # Format output
        if isinstance(value, bool):
            value_str = "true" if value else "false"
        elif isinstance(value, str) and not value:
            value_str = "(empty)"
        else:
            value_str = str(value)
        
        console.print(f"[cyan]{key}[/cyan] = {value_str}")
        
    except Exception as e:
        error(f"Error getting configuration value: {e}")
        raise typer.Exit(1)

@app.command()
def set(
    key: str = typer.Argument(..., help="Configuration key (e.g., server.port)"),
    value: str = typer.Argument(..., help="Configuration value"),
    ctx: typer.Context = None
):
    """Set a configuration value"""
    if ctx is None:
        ctx = typer.Context(set)
    cli_state = ctx.obj
    
    try:
        # Parse the value to appropriate type
        parsed_value = _parse_config_value(cli_state.settings, key, value)
        
        # Set the value in settings
        success_flag = _set_nested_value(cli_state.settings, key, parsed_value)
        
        if not success_flag:
            error(f"Invalid configuration key: {key}")
            warning("Use 'sdh config show' to see available keys")
            raise typer.Exit(1)
        
        # Save configuration to file
        save_config(cli_state.settings)
        
        success("Configuration updated:")
        console.print(f"  [cyan]{key}[/cyan] = {parsed_value}")
        console.print()
        warning("Restart the service for changes to take effect")
        
    except ValueError as e:
        error(f"Invalid value: {e}")
        raise typer.Exit(1)
    except Exception as e:
        error(f"Error setting configuration value: {e}")
        raise typer.Exit(1)

@app.command()
def path():
    """Show configuration file path"""
    config_path = get_config_file_path()
    console.print(f"Configuration file: [cyan]{config_path}[/cyan]")
    if config_path.exists():
        console.print("Status: [green]exists[/green]")
    else:
        console.print("Status: [yellow]not found (using defaults)[/yellow]")

@app.command()
def init(
    ctx: typer.Context,
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite existing configuration")
):
    """Initialize configuration file"""
    cli_state = ctx.obj
    config_path = get_config_file_path()
    
    if config_path.exists() and not force:
        warning(f"Configuration file already exists at: {config_path}")
        console.print()
        if not typer.confirm("Overwrite existing configuration?"):
            info("Configuration initialization cancelled.")
            return
    
    try:
        # Create configuration with current settings
        save_config(cli_state.settings)
        success(f"Configuration file created successfully: {config_path}")
        console.print()
        console.print(f"[cyan]Depot directory:[/cyan] {cli_state.settings.depot_dir}")
        console.print()
        info("You can now edit the configuration file to customize your settings.")
        
    except Exception as e:
        error(f"Failed to create configuration file: {e}")
        raise typer.Exit(1)

def _get_nested_value(settings, key: str):
    """Get nested configuration value using dot notation"""
    parts = key.split('.')
    current = settings
    
    for part in parts:
        if hasattr(current, part):
            current = getattr(current, part)
        else:
            return None
    
    return current

def _set_nested_value(settings, key: str, value) -> bool:
    """Set nested configuration value using dot notation"""
    parts = key.split('.')
    current = settings
    
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
            settings._resolve_paths()
        return True
    
    return False

def _parse_config_value(settings, key: str, value: str):
    """Parse string value to appropriate type based on key"""
    # Get current value to determine type
    current_value = _get_nested_value(settings, key)
    
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
