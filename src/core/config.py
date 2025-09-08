"""
Configuration management for SD-Host
"""

from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings"""
    
    # App settings
    app_name: str = "SD-Host"
    app_version: str = "0.1.0"
    debug: bool = False
    
    # Server settings
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Database settings
    database_url: str = "sqlite+aiosqlite:///./data/sd_host.db"
    
    # Storage settings
    models_dir: str = "./models"
    output_dir: str = "./output"
    temp_dir: str = "./temp"
    
    # Civitai settings
    civitai_api_key: Optional[str] = "c166827d7f1cda8cd073aeb2796552ae"  # Default API key
    civitai_base_url: str = "https://civitai.com/api/v1"
    
    # Proxy settings
    http_proxy: Optional[str] = None
    https_proxy: Optional[str] = None
    
    # File settings
    max_file_size: int = 10 * 1024 * 1024 * 1024  # 10GB
    allowed_extensions: list = [".safetensors", ".ckpt", ".pt", ".bin", ".pth"]
    
    # API settings
    api_prefix: str = "/api"
    cors_origins: list = ["*"]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get settings instance"""
    return settings
