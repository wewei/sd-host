"""
Download Manager - 处理文件下载和断点续传逻辑
"""

import asyncio
import aiofiles
import aiohttp
import hashlib
import os
from typing import Dict, Any, Optional, Callable
from datetime import datetime
import ssl

from core.config import get_settings


class DownloadManager:
    """处理文件下载和断点续传的核心类"""
    
    def __init__(self):
        self.settings = get_settings()
        self.cancellation_flags: Dict[str, str] = {}  # hash -> action (cancel/pause)
    
    def set_cancellation_flag(self, tracking_hash: str, action: str):
        """设置取消/暂停标志"""
        self.cancellation_flags[tracking_hash] = action
    
    def clear_cancellation_flag(self, tracking_hash: str):
        """清除取消/暂停标志"""
        if tracking_hash in self.cancellation_flags:
            del self.cancellation_flags[tracking_hash]
    
    async def download_with_resume(
        self, 
        tracking_hash: str,
        url: str,
        filename: str,
        expected_size: int,
        expected_hash: Optional[str] = None,
        temp_file_path: Optional[str] = None,
        final_file_path: Optional[str] = None,
        resume_position: int = 0,
        progress_callback: Optional[Callable] = None
    ) -> Optional[str]:
        """
        下载文件并支持断点续传
        
        Args:
            tracking_hash: 跟踪哈希
            url: 下载URL
            filename: 文件名
            expected_size: 预期文件大小
            expected_hash: 预期文件哈希
            temp_file_path: 临时文件路径
            final_file_path: 最终文件路径
            resume_position: 断点续传位置
            progress_callback: 进度回调函数
            
        Returns:
            下载完成的文件哈希，失败返回None
        """
        try:
            # 确定文件路径
            if not final_file_path:
                if expected_hash:
                    final_file_path = os.path.join(self.settings.models_dir, f"{expected_hash.lower()}.safetensors")
                else:
                    final_file_path = os.path.join(self.settings.models_dir, filename)
            
            if not temp_file_path:
                temp_file_path = f"{final_file_path}.downloading"
            
            # 检查已存在的部分下载
            if resume_position == 0 and os.path.exists(temp_file_path):
                resume_position = os.path.getsize(temp_file_path)
                print(f"Found partial download: {resume_position} bytes")
            
            # 初始化下载状态
            downloaded_size = resume_position
            start_time = datetime.utcnow()
            last_update_time = start_time
            hasher = hashlib.sha256()
            
            # 如果有已下载的部分，先计算其哈希
            if resume_position > 0:
                try:
                    with open(temp_file_path, 'rb') as existing_file:
                        while True:
                            chunk = existing_file.read(8192)
                            if not chunk:
                                break
                            hasher.update(chunk)
                    print(f"Calculated hash for existing {resume_position} bytes")
                except Exception as e:
                    print(f"Error reading existing file for hash: {e}")
                    resume_position = 0
                    downloaded_size = 0
                    hasher = hashlib.sha256()
            
            # 创建HTTP会话
            session_config = self._create_session_config()
            proxy_config = self._get_proxy_config()
            
            print(f"Starting download from: {url}")
            print(f"Resume position: {resume_position}")
            print(f"Expected size: {expected_size} bytes")
            print(f"Temp file: {temp_file_path}")
            print(f"Final file: {final_file_path}")
            
            # 准备请求头
            headers = {}
            if resume_position > 0:
                headers['Range'] = f'bytes={resume_position}-'
            
            async with aiohttp.ClientSession(**session_config) as session:
                proxy = proxy_config.get("https", proxy_config.get("http"))
                async with session.get(url, headers=headers, proxy=proxy) as response:
                    print(f"Download response status: {response.status}")
                    
                    # 处理不同的响应码
                    if response.status == 206:  # 部分内容（断点续传成功）
                        print("Resume successful")
                    elif response.status == 200:  # 完整内容
                        if resume_position > 0:
                            print("Server doesn't support resume, starting from beginning")
                            resume_position = 0
                            downloaded_size = 0
                            hasher = hashlib.sha256()
                    else:
                        error_text = await response.text()
                        print(f"Download error: {error_text}")
                        return None
                    
                    # 确定文件打开模式
                    file_mode = 'ab' if resume_position > 0 and response.status == 206 else 'wb'
                    
                    async with aiofiles.open(temp_file_path, file_mode) as file:
                        async for chunk in response.content.iter_chunked(8192):
                            # 检查取消/暂停标志
                            if tracking_hash in self.cancellation_flags:
                                action = self.cancellation_flags[tracking_hash]
                                if action == "cancel":
                                    print(f"Download cancelled by user")
                                    await file.close()
                                    if os.path.exists(temp_file_path):
                                        os.remove(temp_file_path)
                                    return None
                                elif action == "pause":
                                    print(f"Download paused by user")
                                    return None
                            
                            await file.write(chunk)
                            hasher.update(chunk)
                            downloaded_size += len(chunk)
                            
                            # 更新进度
                            current_time = datetime.utcnow()
                            if (current_time - last_update_time).total_seconds() >= 1.0:
                                if progress_callback:
                                    elapsed = (current_time - start_time).total_seconds()
                                    speed = (downloaded_size - resume_position) / elapsed if elapsed > 0 else 0
                                    eta_seconds = None
                                    if speed > 0:
                                        remaining_bytes = expected_size - downloaded_size
                                        eta_seconds = int(remaining_bytes / speed)
                                    
                                    await progress_callback(
                                        downloaded_size=downloaded_size,
                                        total_size=expected_size,
                                        speed=speed,
                                        eta_seconds=eta_seconds
                                    )
                                last_update_time = current_time
            
            # 验证下载完整性
            if downloaded_size < expected_size:
                print(f"Download incomplete: {downloaded_size}/{expected_size} bytes")
                return None
            
            # 计算最终哈希
            final_hash = hasher.hexdigest().upper()
            
            # 验证哈希（如果提供）
            if expected_hash and final_hash != expected_hash.upper():
                print(f"Hash mismatch: expected {expected_hash}, got {final_hash}")
                return None
            
            # 移动临时文件到最终位置
            if os.path.exists(final_file_path):
                os.remove(final_file_path)
            os.rename(temp_file_path, final_file_path)
            
            print(f"Download completed successfully: {final_file_path}")
            print(f"File hash: {final_hash}")
            
            return final_hash
            
        except Exception as e:
            print(f"Download error: {e}")
            return None
    
    def _create_session_config(self) -> Dict[str, Any]:
        """创建aiohttp会话配置"""
        session_kwargs = {
            'timeout': aiohttp.ClientTimeout(total=300, connect=30),
            'connector': aiohttp.TCPConnector(limit=10, limit_per_host=2)
        }
        
        # SSL配置
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        session_kwargs['connector'] = aiohttp.TCPConnector(
            ssl=ssl_context,
            limit=10,
            limit_per_host=2
        )
        
        # 如果配置了代理，启用trust_env
        proxy_config = self._get_proxy_config()
        if proxy_config:
            session_kwargs['trust_env'] = True
        
        return session_kwargs
    
    def _get_proxy_config(self) -> Dict[str, str]:
        """获取代理配置"""
        proxy_config = {}
        
        # 检查设置
        if hasattr(self.settings, 'proxy'):
            if hasattr(self.settings.proxy, 'http_proxy') and self.settings.proxy.http_proxy:
                proxy_config["http"] = self.settings.proxy.http_proxy
            if hasattr(self.settings.proxy, 'https_proxy') and self.settings.proxy.https_proxy:
                proxy_config["https"] = self.settings.proxy.https_proxy
        
        # 检查环境变量
        import os
        if not proxy_config.get("http"):
            proxy_config["http"] = os.getenv("HTTP_PROXY") or os.getenv("http_proxy")
        if not proxy_config.get("https"):
            proxy_config["https"] = os.getenv("HTTPS_PROXY") or os.getenv("https_proxy")
        
        # 清理空值
        proxy_config = {k: v for k, v in proxy_config.items() if v}
        
        return proxy_config
