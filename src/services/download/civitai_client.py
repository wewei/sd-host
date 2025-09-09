"""
CivitAI API Client - 处理与CivitAI API的交互
"""

import aiohttp
import ssl
from typing import Dict, Any, Optional
from core.config import get_settings


class CivitaiApiClient:
    """CivitAI API客户端"""
    
    def __init__(self):
        self.settings = get_settings()
        self.base_url = self.settings.civitai.base_url
        self.api_key = self.settings.civitai.api_key
    
    async def get_model_info(self, model_id: str, version_id: str) -> Optional[Dict[str, Any]]:
        """获取模型信息"""
        try:
            session_config = self._create_session_config()
            proxy_config = self._get_proxy_config()
            
            url = f"{self.base_url}/api/v1/model-versions/{version_id}"
            print(f"Fetching model info from: {url}")
            
            async with aiohttp.ClientSession(**session_config) as session:
                proxy = proxy_config.get("https", proxy_config.get("http"))
                async with session.get(url, proxy=proxy) as response:
                    print(f"CivitAI API response status: {response.status}")
                    
                    if response.status == 200:
                        data = await response.json()
                        print(f"Successfully fetched model info for version {version_id}")
                        return data
                    else:
                        error_text = await response.text()
                        print(f"CivitAI API error: {error_text}")
                        return None
                        
        except Exception as e:
            print(f"Error fetching model info: {e}")
            return None
    
    def extract_download_info(self, model_info: Dict[str, Any]) -> Dict[str, Any]:
        """从模型信息中提取下载信息"""
        try:
            # 获取模型数据
            model_data = model_info.get("model", {})
            version_data = model_info
            
            # 查找主要文件
            files = version_data.get("files", [])
            if not files:
                raise ValueError("No files found in model version")
            
            # 找到主要模型文件（通常是第一个safetensors文件）
            primary_file = None
            for file_info in files:
                if file_info.get("primary", False) or file_info["name"].endswith(".safetensors"):
                    primary_file = file_info
                    break
            
            if not primary_file:
                # 如果没有找到主要文件，使用第一个文件
                primary_file = files[0]
                print("Warning: No primary .safetensors file found, using first file")
            
            if not primary_file:
                raise ValueError("No files found in model version")
            
            return {
                "download_url": primary_file["downloadUrl"],
                "filename": primary_file["name"],
                "size": primary_file.get("sizeKB", 0) * 1024,  # Convert KB to bytes
                "hash": primary_file.get("hashes", {}).get("SHA256", ""),
                "model_name": model_data["name"],
                "version_name": version_data["name"],
                "model_type": model_data.get("type", "checkpoint").lower(),
                "base_model": version_data.get("baseModel", ""),
                "description": model_data.get("description", ""),
                "tags": model_data.get("tags", []),
                "images": version_data.get("images", [])
            }
            
        except Exception as e:
            print(f"Error extracting download info: {e}")
            raise
    
    def _create_session_config(self) -> Dict[str, Any]:
        """创建aiohttp会话配置"""
        session_kwargs = {
            'timeout': aiohttp.ClientTimeout(total=30, connect=10),
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
