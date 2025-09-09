"""
Download Status Enum - 下载任务状态枚举
"""

from enum import Enum


class DownloadStatus(str, Enum):
    """下载任务状态"""
    PENDING = "pending"
    DOWNLOADING = "downloading"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
