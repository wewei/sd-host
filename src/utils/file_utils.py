"""
Utility functions for file operations
"""

import hashlib
import os
import aiofiles
from typing import Optional


async def calculate_file_hash(file_path: str) -> Optional[str]:
    """Calculate SHA256 hash of a file"""
    try:
        hasher = hashlib.sha256()
        async with aiofiles.open(file_path, 'rb') as file:
            while chunk := await file.read(8192):
                hasher.update(chunk)
        return hasher.hexdigest()
    except Exception as e:
        print(f"Error calculating file hash: {e}")
        return None


def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"


def ensure_directory_exists(directory_path: str):
    """Ensure directory exists, create if not"""
    os.makedirs(directory_path, exist_ok=True)


def get_file_extension(filename: str) -> str:
    """Get file extension from filename"""
    return os.path.splitext(filename)[1].lower()


def is_model_file(filename: str) -> bool:
    """Check if file is a valid model file"""
    valid_extensions = {'.safetensors', '.ckpt', '.pt', '.bin', '.pth'}
    return get_file_extension(filename) in valid_extensions
