#!/usr/bin/env python3
"""
SD-Host API Service Entry Point
Convenience wrapper for starting the API server from project root
"""

import sys
import os
from pathlib import Path

# Add src to Python path
project_root = Path(__file__).parent.absolute()
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

# Import and run the API
if __name__ == "__main__":
    from api.main import app, get_settings
    import uvicorn
    
    settings = get_settings()
    
    print(f"{settings.app_name}: Stable Diffusion RESTful API Service")
    print(f"Version: {settings.app_version}")
    print("Starting server from project root...")
    
    uvicorn.run(
        app,
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info"
    )
