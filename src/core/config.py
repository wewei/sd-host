"""
Configuration management for SD-Host
"""

import os
import yaml
from pathlib import Path
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
import platform


class ServerConfig(BaseModel):
    """Server configuration"""
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    workers: int = 1
    reload: bool = False


class StableDiffusionConfig(BaseModel):
    """Stable Diffusion configuration"""
    model_config = {"protected_namespaces": ()}
    
    model_name: str = "runwayml/stable-diffusion-v1-5"
    model_path: Optional[str] = None
    device: str = "auto"
    device_id: int = 0
    precision: str = "fp16"
    attention_slicing: bool = True
    memory_efficient_attention: bool = True
    cpu_offload: bool = False
    default_width: int = 512
    default_height: int = 512
    default_steps: int = 20
    default_cfg_scale: float = 7.5
    default_sampler: str = "DPMSolverMultistepScheduler"
    safety_checker: bool = True
    nsfw_filter: bool = True


class StorageConfig(BaseModel):
    """Storage configuration"""
    depot_dir: str = Field(default_factory=lambda: get_default_depot_dir())
    models_dir: Optional[str] = None
    output_dir: Optional[str] = None
    data_dir: Optional[str] = None
    database_url: Optional[str] = None
    max_images: int = 1000
    cleanup_interval: int = 3600
    image_retention_days: int = 7


class APIConfig(BaseModel):
    """API configuration"""
    rate_limit_requests: int = 10
    rate_limit_window: int = 60
    timeout: int = 300
    max_request_size: int = 10485760  # 10MB
    cors_origins: list = ["*"]
    cors_methods: list = ["GET", "POST", "PUT", "DELETE"]
    cors_headers: list = ["*"]
    api_prefix: str = "/api"


class CivitaiConfig(BaseModel):
    """Civitai configuration"""
    api_key: Optional[str] = "c166827d7f1cda8cd073aeb2796552ae"
    base_url: str = "https://civitai.com/api/v1"


class ProxyConfig(BaseModel):
    """Proxy configuration"""
    http_proxy: Optional[str] = None
    https_proxy: Optional[str] = None


class LoggingConfig(BaseModel):
    """Logging configuration"""
    level: str = "INFO"
    format: str = "structured"
    file: Optional[str] = None
    max_size: int = 10485760  # 10MB
    backup_count: int = 5


class SecurityConfig(BaseModel):
    """Security configuration"""
    api_key_enabled: bool = False
    api_key: str = ""
    ssl_enabled: bool = False
    ssl_cert_file: str = ""
    ssl_key_file: str = ""


class MonitoringConfig(BaseModel):
    """Monitoring configuration"""
    health_check_enabled: bool = True
    metrics_enabled: bool = False
    metrics_endpoint: str = "/metrics"
    track_performance: bool = True


class FileConfig(BaseModel):
    """File handling configuration"""
    max_file_size: int = 10 * 1024 * 1024 * 1024  # 10GB
    allowed_extensions: list = [".safetensors", ".ckpt", ".pt", ".bin", ".pth"]


class Settings(BaseModel):
    """Application settings"""
    
    # App metadata
    app_name: str = "SD-Host"
    app_version: str = "0.1.0"
    
    # Configuration sections
    server: ServerConfig = Field(default_factory=ServerConfig)
    stable_diffusion: StableDiffusionConfig = Field(default_factory=StableDiffusionConfig)
    storage: StorageConfig = Field(default_factory=StorageConfig)
    api: APIConfig = Field(default_factory=APIConfig)
    civitai: CivitaiConfig = Field(default_factory=CivitaiConfig)
    proxy: ProxyConfig = Field(default_factory=ProxyConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    monitoring: MonitoringConfig = Field(default_factory=MonitoringConfig)
    file: FileConfig = Field(default_factory=FileConfig)
    
    def __init__(self, **data):
        super().__init__(**data)
        self._resolve_paths()
    
    def _resolve_paths(self):
        """Resolve and set up directory paths"""
        depot_dir = Path(self.storage.depot_dir)
        
        # Always recalculate depot subdirectories based on current depot_dir
        self.storage.models_dir = str(depot_dir / "models")
        self.storage.output_dir = str(depot_dir / "output")
        self.storage.data_dir = str(depot_dir / "data")
        
        # Set up database URL
        self.storage.database_url = f"sqlite+aiosqlite:///{self.storage.data_dir}/sd_host.db"
        
        # Set up logging file
        self.logging.file = str(depot_dir / "logs" / "sd_host.log")
        
        # Set up stable diffusion model path if not set
        if not self.stable_diffusion.model_path:
            self.stable_diffusion.model_path = str(Path(self.storage.models_dir) / self.stable_diffusion.model_name)
    
    @property
    def depot_dir(self) -> str:
        """Get depot directory path"""
        return self.storage.depot_dir
    
    @property
    def models_dir(self) -> str:
        """Get models directory path"""
        return self.storage.models_dir
    
    @property
    def output_dir(self) -> str:
        """Get output directory path"""
        return self.storage.output_dir
    
    @property
    def data_dir(self) -> str:
        """Get data directory path"""
        return self.storage.data_dir
    
    @property
    def database_url(self) -> str:
        """Get database URL"""
        return self.storage.database_url
    
    @property
    def host(self) -> str:
        """Get server host"""
        return self.server.host
    
    @property
    def port(self) -> int:
        """Get server port"""
        return self.server.port
    
    @property
    def debug(self) -> bool:
        """Get debug mode"""
        return self.server.debug
    
    @property
    def cors_origins(self) -> list:
        """Get CORS origins"""
        return self.api.cors_origins


def get_default_depot_dir() -> str:
    """Get default depot directory"""
    # Check environment variable first
    depot_dir = os.environ.get("SDH_DEPOT")
    if depot_dir:
        return depot_dir
    
    # Default to user home directory
    home_dir = Path.home()
    return str(home_dir / "sd-host" / "depot")


def get_config_file_path() -> Path:
    """Get configuration file path"""
    home_dir = Path.home()
    return home_dir / "sd-host" / "config.yml"


def load_config(config_path: Optional[str] = None, depot_dir: Optional[str] = None) -> Settings:
    """Load configuration from file"""
    
    # Override depot directory if provided (takes precedence)
    if depot_dir:
        os.environ["SDH_DEPOT"] = depot_dir
    
    if config_path:
        config_file = Path(config_path)
    else:
        config_file = get_config_file_path()
    
    # Load configuration from file if it exists
    config_data = {}
    if config_file.exists():
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f) or {}
        except Exception as e:
            print(f"Warning: Could not load config file {config_file}: {e}")
            print("Using default configuration")
    
    # Override depot in config data if provided via command line
    if depot_dir:
        if "storage" not in config_data:
            config_data["storage"] = {}
        config_data["storage"]["depot_dir"] = depot_dir
    
    # Create settings instance
    settings = Settings(**config_data)
    
    # Ensure directories exist
    ensure_directories(settings)
    
    return settings


def ensure_directories(settings: Settings):
    """Ensure all required directories exist"""
    directories = [
        settings.depot_dir,
        settings.models_dir,
        settings.output_dir,
        settings.data_dir,
        str(Path(settings.logging.file).parent),
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)


def save_config(settings: Settings, config_path: Optional[str] = None):
    """Save configuration to file"""
    if config_path:
        config_file = Path(config_path)
    else:
        config_file = get_config_file_path()
    
    # Ensure config directory exists
    config_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Convert settings to dict for YAML output
    config_data = settings.model_dump(exclude_none=True)
    
    try:
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(config_data, f, default_flow_style=False, allow_unicode=True, indent=2)
    except Exception as e:
        raise RuntimeError(f"Could not save config to {config_file}: {e}")


# Global settings instance
_settings: Optional[Settings] = None


def get_settings(config_path: Optional[str] = None, depot_dir: Optional[str] = None) -> Settings:
    """Get settings instance"""
    global _settings
    if _settings is None:
        _settings = load_config(config_path, depot_dir)
    return _settings


def reload_settings(config_path: Optional[str] = None, depot_dir: Optional[str] = None) -> Settings:
    """Reload settings from configuration"""
    global _settings
    _settings = load_config(config_path, depot_dir)
    return _settings
