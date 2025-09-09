"""
Civitai integration service for downloading models - Refactored Version
"""

import asyncio
from typing import Dict, Any, Optional, AsyncGenerator, List
from datetime import datetime

from models.entities import Model, Tag, ModelTag
from models.schemas import CivitaiAddResponse, DownloadProgressData, ModelResource
from core.database import AsyncSession
from core.config import get_settings
from services.download import (
    DownloadStatus, DownloadManager, DownloadTaskDatabase, 
    TaskManager, CivitaiApiClient
)


class CivitaiService:
    """Service for downloading models from Civitai"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.settings = get_settings()
        
        # 初始化下载相关组件
        self.download_manager = DownloadManager()
        self.db_ops = DownloadTaskDatabase(session)
        self.task_manager = TaskManager(self.db_ops, self.download_manager)
        self.api_client = CivitaiApiClient()
    
    async def initialize_from_database(self):
        """Initialize service by loading existing download tasks from database"""
        await self.task_manager.initialize_from_database()
    
    async def add_model_from_civitai(self, model_id: str, version_id: str) -> CivitaiAddResponse:
        """Start downloading a model from Civitai with database persistence"""
        try:
            # Get model info from Civitai API
            model_info = await self.api_client.get_model_info(model_id, version_id)
            
            if not model_info:
                raise ValueError("Failed to fetch model information from Civitai")
            
            # Extract download info
            download_info = self.api_client.extract_download_info(model_info)
            
            # Create persistent download task in database
            tracking_hash = await self.task_manager.create_download_task(model_info, download_info)
            
            # Start background download
            asyncio.create_task(self.task_manager.start_download(tracking_hash, download_info, model_info))
            
            return CivitaiAddResponse(
                hash=tracking_hash,
                status="downloading",
                tracking_url=f"/api/models/add-from-civitai/{tracking_hash}"
            )
            
        except Exception as e:
            raise ValueError(f"Failed to start model download: {str(e)}")
    
    async def get_download_progress(self, tracking_hash: str) -> AsyncGenerator[str, None]:
        """SSE endpoint for tracking download progress"""
        while True:
            task_data = self.task_manager.get_task(tracking_hash)
            if task_data:
                progress_data = DownloadProgressData(
                    status=task_data["status"],
                    progress=task_data.get("progress"),
                    speed=task_data.get("speed"),
                    eta=task_data.get("eta"),
                    model_info=task_data.get("model_info"),
                    error=task_data.get("error")
                )
                
                yield f"data: {progress_data.json()}\n\n"
                
                # If completed or failed, clean up and stop
                if task_data["status"] in ["completed", "failed"]:
                    await asyncio.sleep(1)  # Give client time to receive final message
                    break
            else:
                # Task not found
                error_data = DownloadProgressData(
                    status="failed",
                    error="Task not found"
                )
                yield f"data: {error_data.json()}\n\n"
                break
            
            await asyncio.sleep(1)
    
    async def resume_existing_downloads(self):
        """Resume all paused downloads from database"""
        await self.task_manager.resume_existing_downloads()
    
    # ==================== Task Management Methods ====================
    
    async def get_all_download_tasks(self) -> List[Dict[str, Any]]:
        """Get all download tasks with their current status"""
        return self.task_manager.get_all_tasks()
    
    async def get_download_task(self, tracking_hash: str) -> Optional[Dict[str, Any]]:
        """Get a specific download task by hash"""
        return self.task_manager.get_task(tracking_hash)
    
    async def pause_download_task(self, tracking_hash: str) -> bool:
        """Pause a download task"""
        return await self.task_manager.pause_task(tracking_hash)
    
    async def resume_download_task(self, tracking_hash: str) -> bool:
        """Resume a paused download task"""
        return await self.task_manager.resume_task(tracking_hash)
    
    async def cancel_download_task(self, tracking_hash: str) -> bool:
        """Cancel a download task"""
        return await self.task_manager.cancel_task(tracking_hash)
    
    async def remove_download_task(self, tracking_hash: str) -> bool:
        """Remove a completed, failed, or cancelled download task"""
        return await self.task_manager.remove_task(tracking_hash)
    
    async def clear_completed_download_tasks(self) -> bool:
        """Remove all completed, failed, and cancelled download tasks"""
        return await self.task_manager.clear_completed_tasks()
    
    # ==================== Mock Task Creation ====================
    
    async def create_mock_download_task(self, model_name: str = "Test Model", version_name: str = "v1.0") -> str:
        """Create a mock download task for testing purposes"""
        import hashlib
        
        # Generate a unique hash for the mock task
        content_for_hash = f"mock_{model_name}_{version_name}_{datetime.utcnow().isoformat()}"
        tracking_hash = hashlib.sha256(content_for_hash.encode()).hexdigest()
        
        # Create mock model and download info
        model_info = {
            "id": "mock_version_id",
            "modelId": "mock_model_id",
            "model": {
                "name": model_name,
                "type": "checkpoint"
            },
            "name": version_name
        }
        
        download_info = {
            "download_url": "https://mock.example.com/model.safetensors",
            "filename": f"{model_name.lower().replace(' ', '_')}.safetensors",
            "size": 128 * 1024 * 1024,  # 128MB
            "hash": tracking_hash[:64],  # Use first 64 chars as file hash
            "model_name": model_name,
            "version_name": version_name,
            "model_type": "checkpoint"
        }
        
        # Create task in database
        await self.task_manager.create_download_task(model_info, download_info)
        
        # Set mock progress
        await self.task_manager.update_task_progress(
            tracking_hash, 
            downloaded_size=32 * 1024 * 1024,  # 32MB downloaded
            total_size=128 * 1024 * 1024,      # 128MB total
            speed=2.5 * 1024 * 1024,           # 2.5 MB/s
            eta_seconds=15                      # 15 seconds remaining
        )
        
        await self.task_manager.update_task_status(tracking_hash, DownloadStatus.DOWNLOADING)
        
        print(f"Mock download task created: {tracking_hash}")
        return tracking_hash
    
    # ==================== Model Database Operations ====================
    
    async def save_model_to_db(self, file_hash: str, download_info: Dict[str, Any], model_info: Dict[str, Any]) -> Optional[ModelResource]:
        """Save downloaded model to database"""
        try:
            # Check if model already exists
            from sqlalchemy import select
            stmt = select(Model).where(Model.hash == file_hash)
            result = await self.session.execute(stmt)
            existing_model = result.scalar_one_or_none()
            
            if existing_model:
                print(f"Model {file_hash} already exists in database")
                # Convert to resource
                from services.model_service import ModelService
                model_service = ModelService(self.session)
                response = await model_service.get_model_by_hash(file_hash)
                return response.data if response else None
            
            # Create new model
            model = Model(
                hash=file_hash,
                name=download_info.get("model_name", "Unknown Model"),
                model_type=download_info.get("model_type", "checkpoint"),
                base_model=download_info.get("base_model", ""),
                size=download_info.get("size", 0),
                source_url=download_info.get("download_url", ""),
                description=download_info.get("description", "")
            )
            
            self.session.add(model)
            await self.session.flush()
            
            # Add tags if any
            tags = download_info.get("tags", [])
            for tag_name in tags:
                if isinstance(tag_name, dict):
                    tag_name = tag_name.get("name", "")
                
                if not tag_name:
                    continue
                
                # Check if tag exists
                tag_stmt = select(Tag).where(Tag.name == tag_name)
                tag_result = await self.session.execute(tag_stmt)
                tag = tag_result.scalar_one_or_none()
                
                if not tag:
                    tag = Tag(name=tag_name)
                    self.session.add(tag)
                    await self.session.flush()
                
                # Create model-tag association
                model_tag = ModelTag(model_hash=file_hash, tag_name=tag_name)
                self.session.add(model_tag)
            
            await self.session.commit()
            
            # Convert to resource
            from services.model_service import ModelService
            model_service = ModelService(self.session)
            response = await model_service.get_model_by_hash(file_hash)
            return response.data if response else None
            
        except Exception as e:
            print(f"ERROR in save_model_to_db: {str(e)}")
            await self.session.rollback()
            raise
