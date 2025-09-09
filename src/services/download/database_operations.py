"""
Database Operations - 处理下载任务的数据库CRUD操作
"""

import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload

from models.entities import DownloadTask
from core.database import AsyncSession
from .enums import DownloadStatus


class DownloadTaskDatabase:
    """下载任务数据库操作类"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_task(self, tracking_hash: str, model_info: Dict[str, Any], 
                         download_info: Dict[str, Any]) -> DownloadTask:
        """创建新的下载任务"""
        db_task = DownloadTask(
            hash=tracking_hash,
            model_name=download_info.get("model_name", download_info.get("name", "Unknown Model")),
            version_name=download_info.get("version_name", model_info.get("model", {}).get("name", "Unknown")),
            model_type=download_info.get("model_type", download_info.get("type", "checkpoint")),
            source_url=download_info["download_url"],
            source_type="civitai",
            status=DownloadStatus.PENDING,
            total_size=download_info.get("size"),
            civitai_model_id=model_info.get("modelId"),
            civitai_version_id=model_info.get("id"),
            download_metadata=json.dumps({
                "filename": download_info["filename"],
                "expected_hash": download_info.get("hash"),
                "model_info": model_info
            })
        )
        
        self.session.add(db_task)
        await self.session.commit()
        return db_task
    
    async def get_task_by_hash(self, tracking_hash: str) -> Optional[DownloadTask]:
        """根据哈希获取任务"""
        try:
            stmt = select(DownloadTask).where(DownloadTask.hash == tracking_hash)
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            print(f"Error getting task by hash: {e}")
            return None
    
    async def get_unfinished_tasks(self) -> List[DownloadTask]:
        """获取所有未完成的任务"""
        try:
            stmt = select(DownloadTask).where(
                DownloadTask.status.in_(['pending', 'downloading', 'paused'])
            )
            result = await self.session.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            print(f"Error getting unfinished tasks: {e}")
            return []
    
    async def get_paused_tasks(self) -> List[DownloadTask]:
        """获取所有暂停的任务"""
        try:
            stmt = select(DownloadTask).where(DownloadTask.status == DownloadStatus.PAUSED)
            result = await self.session.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            print(f"Error getting paused tasks: {e}")
            return []
    
    async def update_task_progress(self, tracking_hash: str, downloaded_size: int,
                                 total_size: int = None, speed: float = None,
                                 eta_seconds: int = None):
        """更新任务进度"""
        try:
            update_data = {
                DownloadTask.downloaded_size: downloaded_size,
                DownloadTask.resume_position: downloaded_size,
                DownloadTask.updated_at: datetime.utcnow()
            }
            
            if total_size is not None:
                update_data[DownloadTask.total_size] = total_size
            if speed is not None:
                update_data[DownloadTask.download_speed] = speed
            if eta_seconds is not None:
                update_data[DownloadTask.eta_seconds] = eta_seconds
            
            stmt = update(DownloadTask).where(DownloadTask.hash == tracking_hash).values(**update_data)
            await self.session.execute(stmt)
            await self.session.commit()
            
        except Exception as e:
            print(f"Error updating task progress: {e}")
    
    async def update_task_status(self, tracking_hash: str, status: DownloadStatus):
        """更新任务状态"""
        try:
            update_data = {
                DownloadTask.status: status,
                DownloadTask.updated_at: datetime.utcnow()
            }
            
            # 设置特殊时间戳
            if status == DownloadStatus.DOWNLOADING:
                # 检查是否已有started_at
                existing_task = await self.get_task_by_hash(tracking_hash)
                if existing_task and not existing_task.started_at:
                    update_data[DownloadTask.started_at] = datetime.utcnow()
            elif status == DownloadStatus.COMPLETED:
                update_data[DownloadTask.completed_at] = datetime.utcnow()
            
            stmt = update(DownloadTask).where(DownloadTask.hash == tracking_hash).values(**update_data)
            await self.session.execute(stmt)
            await self.session.commit()
            
        except Exception as e:
            print(f"Error updating task status: {e}")
    
    async def update_task_file_paths(self, tracking_hash: str, temp_path: str, final_path: str):
        """更新任务文件路径"""
        try:
            stmt = update(DownloadTask).where(DownloadTask.hash == tracking_hash).values(
                temp_file_path=temp_path,
                final_file_path=final_path,
                updated_at=datetime.utcnow()
            )
            await self.session.execute(stmt)
            await self.session.commit()
        except Exception as e:
            print(f"Error updating task file paths: {e}")
    
    async def set_task_error(self, tracking_hash: str, error_message: str):
        """设置任务错误信息"""
        try:
            stmt = update(DownloadTask).where(DownloadTask.hash == tracking_hash).values(
                error_message=error_message,
                updated_at=datetime.utcnow()
            )
            await self.session.execute(stmt)
            await self.session.commit()
        except Exception as e:
            print(f"Error setting task error: {e}")
    
    async def mark_task_completed(self, tracking_hash: str, file_hash: str):
        """标记任务为已完成"""
        try:
            stmt = update(DownloadTask).where(DownloadTask.hash == tracking_hash).values(
                model_hash=file_hash,
                status=DownloadStatus.COMPLETED,
                completed_at=datetime.utcnow(),
                temp_file_path=None,  # 清空临时文件路径
                updated_at=datetime.utcnow()
            )
            await self.session.execute(stmt)
            await self.session.commit()
        except Exception as e:
            print(f"Error marking task completed: {e}")
    
    async def delete_task(self, tracking_hash: str):
        """删除任务"""
        try:
            stmt = delete(DownloadTask).where(DownloadTask.hash == tracking_hash)
            await self.session.execute(stmt)
            await self.session.commit()
        except Exception as e:
            print(f"Error deleting task: {e}")
    
    async def delete_completed_tasks(self):
        """删除所有已完成的任务"""
        try:
            stmt = delete(DownloadTask).where(
                DownloadTask.status.in_([
                    DownloadStatus.COMPLETED, 
                    DownloadStatus.FAILED, 
                    DownloadStatus.CANCELLED
                ])
            )
            await self.session.execute(stmt)
            await self.session.commit()
        except Exception as e:
            print(f"Error deleting completed tasks: {e}")
    
    async def increment_retry_count(self, tracking_hash: str):
        """增加重试次数"""
        try:
            task = await self.get_task_by_hash(tracking_hash)
            if task and task.can_retry():
                stmt = update(DownloadTask).where(DownloadTask.hash == tracking_hash).values(
                    retry_count=task.retry_count + 1,
                    updated_at=datetime.utcnow()
                )
                await self.session.execute(stmt)
                await self.session.commit()
        except Exception as e:
            print(f"Error incrementing retry count: {e}")
