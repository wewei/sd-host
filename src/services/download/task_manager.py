"""
Task Manager - 处理下载任务的生命周期管理
"""

import asyncio
import hashlib
import time
from typing import Dict, Any, List, Optional
from datetime import datetime

from models.entities import DownloadTask
from .download_manager import DownloadManager
from .database_operations import DownloadTaskDatabase
from .enums import DownloadStatus


class TaskManager:
    """下载任务生命周期管理器"""
    
    def __init__(self, db_ops: DownloadTaskDatabase, download_manager: DownloadManager):
        self.db_ops = db_ops
        self.download_manager = download_manager
        self.active_tasks: Dict[str, Dict[str, Any]] = {}  # 内存中的活动任务
    
    async def initialize_from_database(self):
        """从数据库初始化任务管理器"""
        try:
            # 加载未完成的下载任务
            tasks = await self.db_ops.get_unfinished_tasks()
            
            for task in tasks:
                # 添加到内存会话
                self.active_tasks[task.hash] = {
                    "model_name": task.model_name,
                    "version_name": task.version_name or "Unknown",
                    "status": task.status,
                    "progress": task.progress_percentage,
                    "speed": f"{task.download_speed or 0:.1f} MB/s" if task.download_speed else "0 MB/s",
                    "eta": self._format_eta(task.eta_seconds) if task.eta_seconds else "Unknown",
                    "size": task.total_size or 0,
                    "downloaded": task.downloaded_size,
                    "created_at": task.created_at.isoformat() if task.created_at else datetime.utcnow().isoformat(),
                    "error": task.error_message,
                    "db_task": True,
                    "temp_file_path": task.temp_file_path,
                    "resume_position": task.resume_position,
                    "retry_count": task.retry_count,
                    "source_url": task.source_url,
                    "civitai_model_id": task.civitai_model_id,
                    "civitai_version_id": task.civitai_version_id
                }
            
            print(f"Loaded {len(tasks)} download tasks from database")
            
        except Exception as e:
            print(f"Error loading download tasks from database: {e}")
    
    async def create_download_task(self, model_info: Dict[str, Any], download_info: Dict[str, Any]) -> str:
        """创建新的下载任务"""
        # 生成跟踪哈希
        content_for_hash = f"{download_info['download_url']}{download_info['filename']}{datetime.utcnow().isoformat()}"
        tracking_hash = hashlib.sha256(content_for_hash.encode()).hexdigest()
        
        # 创建数据库记录
        db_task = await self.db_ops.create_task(
            tracking_hash=tracking_hash,
            model_info=model_info,
            download_info=download_info
        )
        
        # 添加到内存会话
        self.active_tasks[tracking_hash] = {
            "model_name": db_task.model_name,
            "version_name": db_task.version_name or "Unknown",
            "status": db_task.status,
            "progress": 0.0,
            "speed": "0 MB/s",
            "eta": "Unknown",
            "size": db_task.total_size or 0,
            "downloaded": 0,
            "created_at": db_task.created_at.isoformat(),
            "error": None,
            "db_task": True
        }
        
        return tracking_hash
    
    async def start_download(self, tracking_hash: str, download_info: Dict[str, Any], model_info: Dict[str, Any]):
        """启动下载任务"""
        try:
            # 更新状态为下载中
            await self.update_task_status(tracking_hash, DownloadStatus.DOWNLOADING)
            
            # 获取任务信息
            db_task = await self.db_ops.get_task_by_hash(tracking_hash)
            if not db_task:
                raise ValueError(f"Task {tracking_hash} not found in database")
            
            # 定义进度回调
            async def progress_callback(downloaded_size: int, total_size: int = None, 
                                     speed: float = None, eta_seconds: int = None):
                await self.update_task_progress(tracking_hash, downloaded_size, total_size, speed, eta_seconds)
            
            # 开始下载
            file_hash = await self.download_manager.download_with_resume(
                tracking_hash=tracking_hash,
                url=download_info["download_url"],
                filename=download_info["filename"],
                expected_size=download_info.get("size", 0),
                expected_hash=download_info.get("hash"),
                temp_file_path=db_task.temp_file_path,
                final_file_path=db_task.final_file_path,
                resume_position=db_task.resume_position,
                progress_callback=progress_callback
            )
            
            if file_hash:
                # 下载成功
                await self.update_task_status(tracking_hash, DownloadStatus.COMPLETED)
                await self.db_ops.mark_task_completed(tracking_hash, file_hash)
                
                # 更新内存状态
                if tracking_hash in self.active_tasks:
                    self.active_tasks[tracking_hash].update({
                        "status": DownloadStatus.COMPLETED,
                        "progress": 100.0,
                        "model_hash": file_hash
                    })
            else:
                # 检查是否被暂停或取消
                current_status = self.active_tasks.get(tracking_hash, {}).get("status")
                if current_status not in [DownloadStatus.CANCELLED, DownloadStatus.PAUSED]:
                    await self.update_task_status(tracking_hash, DownloadStatus.FAILED)
                    await self.db_ops.set_task_error(tracking_hash, "Download failed")
                
        except Exception as e:
            print(f"Download task error: {e}")
            await self.update_task_status(tracking_hash, DownloadStatus.FAILED)
            await self.db_ops.set_task_error(tracking_hash, str(e))
    
    async def update_task_progress(self, tracking_hash: str, downloaded_size: int, 
                                 total_size: int = None, speed: float = None, 
                                 eta_seconds: int = None):
        """更新任务进度"""
        # 更新内存状态
        if tracking_hash in self.active_tasks:
            session_data = self.active_tasks[tracking_hash]
            session_data["downloaded"] = downloaded_size
            if total_size:
                session_data["size"] = total_size
                session_data["progress"] = min(100.0, (downloaded_size / total_size) * 100.0)
            if speed is not None:
                # speed 是字节/秒，转换为 MB/s
                speed_mb_s = speed / (1024 * 1024)
                session_data["speed"] = f"{speed_mb_s:.1f} MB/s"
            if eta_seconds is not None:
                session_data["eta"] = self._format_eta(eta_seconds)
        
        # 减少数据库更新频率，每5秒或进度变化超过1%时才更新
        try:
            should_update_db = False
            if tracking_hash in self.active_tasks:
                last_db_update = getattr(self, '_last_db_updates', {}).get(tracking_hash, 0)
                current_time = time.time()
                progress_pct = session_data.get("progress", 0)
                last_progress = getattr(self, '_last_progress', {}).get(tracking_hash, 0)
                
                # 每5秒更新一次，或者进度变化超过1%
                if (current_time - last_db_update > 5) or (abs(progress_pct - last_progress) > 1):
                    should_update_db = True
                    if not hasattr(self, '_last_db_updates'):
                        self._last_db_updates = {}
                    if not hasattr(self, '_last_progress'):
                        self._last_progress = {}
                    self._last_db_updates[tracking_hash] = current_time
                    self._last_progress[tracking_hash] = progress_pct
            
            # 更新数据库（异步且不阻塞）
            if should_update_db:
                asyncio.create_task(self._update_db_progress_safe(
                    tracking_hash, downloaded_size, total_size, speed, eta_seconds
                ))
        except Exception as e:
            print(f"Error in update_task_progress: {e}")
    
    async def _update_db_progress_safe(self, tracking_hash: str, downloaded_size: int,
                                     total_size: int = None, speed: float = None,
                                     eta_seconds: int = None):
        """安全地更新数据库进度（不阻塞主进程）"""
        try:
            await self.db_ops.update_task_progress(
                tracking_hash, downloaded_size, total_size, speed, eta_seconds
            )
        except Exception as e:
            print(f"Error updating database progress: {e}")
    
    async def update_task_status(self, tracking_hash: str, status: DownloadStatus):
        """更新任务状态"""
        # 更新内存状态
        if tracking_hash in self.active_tasks:
            self.active_tasks[tracking_hash]["status"] = status
        
        # 更新数据库
        await self.db_ops.update_task_status(tracking_hash, status)
    
    async def pause_task(self, tracking_hash: str) -> bool:
        """暂停任务"""
        try:
            if tracking_hash not in self.active_tasks:
                return False
            
            task_data = self.active_tasks[tracking_hash]
            if task_data["status"] != DownloadStatus.DOWNLOADING:
                return False
            
            # 设置暂停标志
            self.download_manager.set_cancellation_flag(tracking_hash, "pause")
            
            # 更新状态
            await self.update_task_status(tracking_hash, DownloadStatus.PAUSED)
            
            return True
        except Exception as e:
            print(f"Error pausing task: {e}")
            return False
    
    async def resume_task(self, tracking_hash: str) -> bool:
        """恢复任务"""
        try:
            if tracking_hash not in self.active_tasks:
                return False
            
            task_data = self.active_tasks[tracking_hash]
            if task_data["status"] != DownloadStatus.PAUSED:
                return False
            
            # 清除暂停标志
            self.download_manager.clear_cancellation_flag(tracking_hash)
            
            # 获取任务信息重新启动
            db_task = await self.db_ops.get_task_by_hash(tracking_hash)
            if db_task and db_task.is_resumable:
                # 从元数据重建下载信息
                metadata = db_task.get_download_metadata_dict()
                download_info = {
                    "download_url": db_task.source_url,
                    "filename": metadata.get("filename", "unknown.safetensors"),
                    "size": db_task.total_size or 0,
                    "hash": metadata.get("expected_hash"),
                    "model_name": db_task.model_name,
                    "version_name": db_task.version_name,
                    "model_type": db_task.model_type or "checkpoint"
                }
                model_info = metadata.get("model_info", {})
                
                # 在后台重新启动下载
                asyncio.create_task(self.start_download(tracking_hash, download_info, model_info))
                return True
            
            return False
        except Exception as e:
            print(f"Error resuming task: {e}")
            return False
    
    async def cancel_task(self, tracking_hash: str) -> bool:
        """取消任务"""
        try:
            if tracking_hash not in self.active_tasks:
                return False
            
            # 设置取消标志
            self.download_manager.set_cancellation_flag(tracking_hash, "cancel")
            
            # 更新状态
            await self.update_task_status(tracking_hash, DownloadStatus.CANCELLED)
            
            return True
        except Exception as e:
            print(f"Error cancelling task: {e}")
            return False
    
    async def remove_task(self, tracking_hash: str) -> bool:
        """移除任务"""
        try:
            if tracking_hash not in self.active_tasks:
                return False
            
            task_data = self.active_tasks[tracking_hash]
            # 只允许移除已完成、失败或取消的任务
            if task_data["status"] not in [DownloadStatus.COMPLETED, DownloadStatus.FAILED, DownloadStatus.CANCELLED]:
                return False
            
            # 从数据库删除
            await self.db_ops.delete_task(tracking_hash)
            
            # 从内存移除
            del self.active_tasks[tracking_hash]
            
            return True
        except Exception as e:
            print(f"Error removing task: {e}")
            return False
    
    async def clear_completed_tasks(self) -> bool:
        """清理已完成的任务"""
        try:
            # 从数据库删除已完成的任务
            await self.db_ops.delete_completed_tasks()
            
            # 从内存移除已完成的任务
            completed_hashes = [
                hash_key for hash_key, task_data in self.active_tasks.items()
                if task_data["status"] in [DownloadStatus.COMPLETED, DownloadStatus.FAILED, DownloadStatus.CANCELLED]
            ]
            
            for hash_key in completed_hashes:
                del self.active_tasks[hash_key]
            
            return True
        except Exception as e:
            print(f"Error clearing completed tasks: {e}")
            return False
    
    def get_all_tasks(self) -> List[Dict[str, Any]]:
        """获取所有任务"""
        tasks = []
        for tracking_hash, session_data in self.active_tasks.items():
            task_info = {
                "type": "download_task",
                "hash": tracking_hash,
                "status": session_data["status"],
                "progress": session_data.get("progress", 0.0),
                "speed": session_data.get("speed", "0 MB/s"),
                "eta": session_data.get("eta", "Unknown"),
                "model_name": session_data.get("model_name", "Unknown"),
                "version_name": session_data.get("version_name", "Unknown"),
                "size": session_data.get("size", 0),
                "downloaded": session_data.get("downloaded", 0),
                "created_at": session_data.get("created_at", datetime.utcnow().isoformat()),
                "error": session_data.get("error")
            }
            tasks.append(task_info)
        return tasks
    
    def get_task(self, tracking_hash: str) -> Optional[Dict[str, Any]]:
        """获取单个任务"""
        if tracking_hash not in self.active_tasks:
            return None
        
        session_data = self.active_tasks[tracking_hash]
        return {
            "type": "download_task",
            "hash": tracking_hash,
            "status": session_data["status"],
            "progress": session_data.get("progress", 0.0),
            "speed": session_data.get("speed", "0 MB/s"),
            "eta": session_data.get("eta", "Unknown"),
            "model_name": session_data.get("model_name", "Unknown"),
            "version_name": session_data.get("version_name", "Unknown"),
            "size": session_data.get("size", 0),
            "downloaded": session_data.get("downloaded", 0),
            "created_at": session_data.get("created_at", datetime.utcnow().isoformat()),
            "error": session_data.get("error")
        }
    
    async def resume_existing_downloads(self):
        """恢复所有暂停的下载"""
        try:
            paused_tasks = await self.db_ops.get_paused_tasks()
            
            for task in paused_tasks:
                if task.is_resumable:
                    print(f"Resuming download: {task.model_name}")
                    # 获取原始下载信息
                    metadata = task.get_download_metadata_dict()
                    download_info = {
                        "download_url": task.source_url,
                        "filename": metadata.get("filename", "unknown.safetensors"),
                        "size": task.total_size or 0,
                        "hash": metadata.get("expected_hash"),
                        "model_name": task.model_name,
                        "version_name": task.version_name,
                        "model_type": task.model_type or "checkpoint"
                    }
                    model_info = metadata.get("model_info", {})
                    
                    # 在后台恢复下载
                    asyncio.create_task(self.start_download(task.hash, download_info, model_info))
                    
            if paused_tasks:
                print(f"Resumed {len(paused_tasks)} paused downloads")
                
        except Exception as e:
            print(f"Error resuming downloads: {e}")
    
    def _format_eta(self, eta_seconds: int) -> str:
        """格式化ETA"""
        if eta_seconds <= 0:
            return "Unknown"
        
        hours = eta_seconds // 3600
        minutes = (eta_seconds % 3600) // 60
        seconds = eta_seconds % 60
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes:02d}:{seconds:02d}"
