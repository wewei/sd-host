"""
Main entry point for SD-Host application
"""

import sys
import os
from contextlib import asynccontextmanager

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from core.database import db_manager
from core.config import get_settings
from api.models import router as models_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    print("Starting SD-Host application...")
    
    # Create database tables
    await db_manager.create_tables()
    print("Database tables created/verified")
    
    yield
    
    # Shutdown
    print("Shutting down SD-Host application...")
    await db_manager.close()


def create_app() -> FastAPI:
    """Create FastAPI application"""
    settings = get_settings()
    
    app = FastAPI(
        title=settings.app_name,
        description="Stable Diffusion RESTful API Service",
        version=settings.app_version,
        lifespan=lifespan
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include routers
    app.include_router(models_router)
    
    @app.get("/")
    async def root():
        return {
            "message": f"{settings.app_name}: Stable Diffusion RESTful API Service",
            "version": settings.app_version,
            "docs": "/docs"
        }
    
    @app.get("/health")
    async def health_check():
        return {"status": "healthy"}
    
    return app


# Create app instance
app = create_app()


if __name__ == "__main__":
    settings = get_settings()
    
    print(f"{settings.app_name}: Stable Diffusion RESTful API Service")
    print(f"Version: {settings.app_version}")
    print("Starting server...")
    
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info"
    )
