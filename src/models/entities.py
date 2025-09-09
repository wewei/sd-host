"""
SQLAlchemy models for the SD-Host application
"""

from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey, Float, CheckConstraint, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional, List
import json

from core.database import Base


class Model(Base):
    """Model entity representing Stable Diffusion models"""
    
    __tablename__ = "models"
    
    # Primary key - SHA256 hash
    hash = Column(String, primary_key=True)
    
    # Core attributes
    name = Column(String, nullable=False)
    model_type = Column(String, nullable=False)  # checkpoint, lora, controlnet, vae, embedding
    base_model = Column(String, nullable=True)   # SD1.5, SDXL, etc.
    size = Column(Integer, nullable=False)       # File size in bytes
    source_url = Column(Text, nullable=True)     # Download source URL
    model_metadata = Column(Text, nullable=True) # JSON metadata (renamed from metadata)
    description = Column(Text, nullable=True)    # Markdown description
    cover_image_hash = Column(String, ForeignKey("images.hash", ondelete="SET NULL"), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    cover_image = relationship("Image", foreign_keys=[cover_image_hash])
    tags = relationship("ModelTag", back_populates="model", cascade="all, delete-orphan")
    
    # Tasks using this model as checkpoint
    checkpoint_tasks = relationship("Task", foreign_keys="Task.checkpoint_hash", back_populates="checkpoint")
    vae_tasks = relationship("Task", foreign_keys="Task.vae_hash", back_populates="vae")
    task_models = relationship("TaskModel", back_populates="model")
    
    # Check constraints
    __table_args__ = (
        CheckConstraint("model_type IN ('checkpoint', 'lora', 'controlnet', 'vae', 'embedding')", name="chk_model_type"),
        CheckConstraint("size > 0", name="chk_size"),
        Index("idx_models_type", "model_type"),
        Index("idx_models_base_model", "base_model"),
        Index("idx_models_created_at", "created_at"),
        Index("idx_models_cover_image", "cover_image_hash"),
        Index("idx_models_name_fts", "name"),
    )
    
    def get_metadata_dict(self) -> dict:
        """Parse metadata JSON string to dict"""
        if self.model_metadata:
            try:
                return json.loads(self.model_metadata)
            except json.JSONDecodeError:
                return {}
        return {}
    
    def set_metadata_dict(self, metadata_dict: dict):
        """Set metadata from dict"""
        self.model_metadata = json.dumps(metadata_dict) if metadata_dict else None


class Image(Base):
    """Image entity representing generated or model cover images"""
    
    __tablename__ = "images"
    
    # Primary key - SHA256 hash
    hash = Column(String, primary_key=True)
    
    # Core attributes
    task_id = Column(String, ForeignKey("tasks.id", ondelete="SET NULL"), nullable=True)
    width = Column(Integer, nullable=False)
    height = Column(Integer, nullable=False)
    size = Column(Integer, nullable=False)
    seed = Column(Integer, nullable=True)
    
    # Timestamp
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    task = relationship("Task", back_populates="images")
    tags = relationship("ImageTag", back_populates="image", cascade="all, delete-orphan")
    
    # Check constraints
    __table_args__ = (
        CheckConstraint("width > 0 AND height > 0", name="chk_dimensions"),
        CheckConstraint("size > 0", name="chk_image_size"),
        Index("idx_images_task_id", "task_id"),
        Index("idx_images_dimensions", "width", "height"),
        Index("idx_images_created_at", "created_at"),
        Index("idx_images_seed", "seed"),
    )


class Task(Base):
    """Task entity representing generation requests"""
    
    __tablename__ = "tasks"
    
    # Primary key - UUID
    id = Column(String, primary_key=True)
    
    # Core attributes
    status = Column(String, nullable=False, default="pending")
    
    # Model associations
    checkpoint_hash = Column(String, ForeignKey("models.hash", ondelete="CASCADE"), nullable=False)
    vae_hash = Column(String, ForeignKey("models.hash", ondelete="SET NULL"), nullable=True)
    
    # Generation parameters
    prompt = Column(Text, nullable=False)
    negative_prompt = Column(Text, default="")
    width = Column(Integer, nullable=False, default=512)
    height = Column(Integer, nullable=False, default=512)
    seed = Column(Integer, default=-1)
    steps = Column(Integer, nullable=False, default=20)
    cfg_scale = Column(Float, nullable=False, default=7.0)
    sampler = Column(String, nullable=False, default="DPM++ 2M Karras")
    batch_size = Column(Integer, nullable=False, default=1)
    
    # Error handling
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    promoted_at = Column(DateTime, default=datetime(1970, 1, 1))  # Default epoch 0
    completed_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    checkpoint = relationship("Model", foreign_keys=[checkpoint_hash])
    vae = relationship("Model", foreign_keys=[vae_hash])
    images = relationship("Image", back_populates="task", cascade="all, delete-orphan")
    task_models = relationship("TaskModel", back_populates="task", cascade="all, delete-orphan")
    tags = relationship("TaskTag", back_populates="task", cascade="all, delete-orphan")
    
    # Check constraints
    __table_args__ = (
        CheckConstraint("status IN ('pending', 'completed', 'failed', 'cancelled')", name="chk_status"),
        CheckConstraint("width > 0 AND height > 0", name="chk_task_dimensions"),
        CheckConstraint("steps > 0 AND steps <= 200", name="chk_steps"),
        CheckConstraint("cfg_scale > 0 AND cfg_scale <= 30", name="chk_cfg_scale"),
        CheckConstraint("batch_size > 0 AND batch_size <= 10", name="chk_batch_size"),
        Index("idx_tasks_status", "status"),
        Index("idx_tasks_checkpoint", "checkpoint_hash"),
        Index("idx_tasks_vae", "vae_hash"),
        Index("idx_tasks_created_at", "created_at"),
        Index("idx_tasks_promoted_at", "promoted_at"),
        Index("idx_tasks_completed_at", "completed_at"),
        Index("idx_tasks_queue", "status", "promoted_at", "created_at", 
              postgresql_where=Column("status") == "pending"),
    )


class TaskModel(Base):
    """Association table for tasks and additional models (LoRA, ControlNet, etc.)"""
    
    __tablename__ = "task_models"
    
    task_id = Column(String, ForeignKey("tasks.id", ondelete="CASCADE"), primary_key=True)
    model_hash = Column(String, ForeignKey("models.hash", ondelete="CASCADE"), primary_key=True)
    weight = Column(Float, default=1.0)
    
    # Relationships
    task = relationship("Task", back_populates="task_models")
    model = relationship("Model", back_populates="task_models")
    
    # Check constraints
    __table_args__ = (
        CheckConstraint("weight >= 0.0 AND weight <= 2.0", name="chk_weight"),
        Index("idx_task_models_task", "task_id"),
        Index("idx_task_models_model", "model_hash"),
    )


class Tag(Base):
    """Tag entity for categorizing models, tasks, and images"""
    
    __tablename__ = "tags"
    
    name = Column(String(20), primary_key=True)
    description = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    model_tags = relationship("ModelTag", back_populates="tag", cascade="all, delete-orphan")
    task_tags = relationship("TaskTag", back_populates="tag", cascade="all, delete-orphan")
    image_tags = relationship("ImageTag", back_populates="tag", cascade="all, delete-orphan")
    
    # Check constraints
    __table_args__ = (
        CheckConstraint("length(name) <= 20 AND length(name) > 0", name="chk_name_length"),
        Index("idx_tags_created_at", "created_at"),
    )


class ModelTag(Base):
    """Association table for models and tags"""
    
    __tablename__ = "model_tags"
    
    model_hash = Column(String, ForeignKey("models.hash", ondelete="CASCADE"), primary_key=True)
    tag_name = Column(String(20), ForeignKey("tags.name", ondelete="CASCADE"), primary_key=True)
    
    # Timestamp
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    model = relationship("Model", back_populates="tags")
    tag = relationship("Tag", back_populates="model_tags")
    
    __table_args__ = (
        Index("idx_model_tags_model", "model_hash"),
        Index("idx_model_tags_tag", "tag_name"),
        Index("idx_model_tags_created_at", "created_at"),
    )


class TaskTag(Base):
    """Association table for tasks and tags"""
    
    __tablename__ = "task_tags"
    
    task_id = Column(String, ForeignKey("tasks.id", ondelete="CASCADE"), primary_key=True)
    tag_name = Column(String(20), ForeignKey("tags.name", ondelete="CASCADE"), primary_key=True)
    
    # Timestamp
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    task = relationship("Task", back_populates="tags")
    tag = relationship("Tag", back_populates="task_tags")
    
    __table_args__ = (
        Index("idx_task_tags_task", "task_id"),
        Index("idx_task_tags_tag", "tag_name"),
        Index("idx_task_tags_created_at", "created_at"),
    )


class ImageTag(Base):
    """Association table for images and tags"""
    
    __tablename__ = "image_tags"
    
    image_hash = Column(String, ForeignKey("images.hash", ondelete="CASCADE"), primary_key=True)
    tag_name = Column(String(20), ForeignKey("tags.name", ondelete="CASCADE"), primary_key=True)
    
    # Timestamp
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    image = relationship("Image", back_populates="tags")
    tag = relationship("Tag", back_populates="image_tags")
    
    __table_args__ = (
        Index("idx_image_tags_image", "image_hash"),
        Index("idx_image_tags_tag", "tag_name"),
        Index("idx_image_tags_created_at", "created_at"),
    )


class DownloadTask(Base):
    """Download task entity for tracking model downloads with resume capability"""
    
    __tablename__ = "download_tasks"
    
    # Primary key - task hash (SHA256 of model + url)
    hash = Column(String, primary_key=True)
    
    # Target model info
    model_hash = Column(String, nullable=True)  # Will be populated when download completes
    model_name = Column(String, nullable=False)
    version_name = Column(String, nullable=True)
    model_type = Column(String, nullable=True)  # checkpoint, lora, etc.
    
    # Download source
    source_url = Column(Text, nullable=False)
    source_type = Column(String, nullable=False, default="civitai")  # civitai, huggingface, etc.
    
    # Download progress
    status = Column(String, nullable=False, default="pending")  # pending, downloading, paused, completed, failed, cancelled
    total_size = Column(Integer, nullable=True)     # Total file size in bytes
    downloaded_size = Column(Integer, nullable=False, default=0)  # Downloaded bytes
    resume_position = Column(Integer, nullable=False, default=0)  # Position for resume
    
    # Speed and timing
    download_speed = Column(Float, nullable=True)   # Current speed in bytes/sec
    eta_seconds = Column(Integer, nullable=True)    # Estimated time remaining
    
    # File management
    temp_file_path = Column(Text, nullable=True)    # Temporary download file path
    final_file_path = Column(Text, nullable=True)   # Final model file path
    
    # Metadata
    civitai_model_id = Column(Integer, nullable=True)
    civitai_version_id = Column(Integer, nullable=True)
    download_metadata = Column(Text, nullable=True)  # JSON metadata
    error_message = Column(Text, nullable=True)      # Error details if failed
    
    # Retry management
    retry_count = Column(Integer, nullable=False, default=0)
    max_retries = Column(Integer, nullable=False, default=3)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    started_at = Column(DateTime, nullable=True)     # When download actually started
    completed_at = Column(DateTime, nullable=True)   # When download completed
    
    # Check constraints
    __table_args__ = (
        CheckConstraint("status IN ('pending', 'downloading', 'paused', 'completed', 'failed', 'cancelled')", name="chk_download_status"),
        CheckConstraint("downloaded_size >= 0", name="chk_downloaded_size"),
        CheckConstraint("resume_position >= 0", name="chk_resume_position"),
        CheckConstraint("total_size IS NULL OR total_size > 0", name="chk_total_size"),
        CheckConstraint("retry_count >= 0", name="chk_retry_count"),
        CheckConstraint("max_retries >= 0", name="chk_max_retries"),
        Index("idx_download_tasks_status", "status"),
        Index("idx_download_tasks_model_hash", "model_hash"),
        Index("idx_download_tasks_created_at", "created_at"),
        Index("idx_download_tasks_source_type", "source_type"),
        Index("idx_download_tasks_civitai_model", "civitai_model_id"),
    )
    
    @property
    def progress_percentage(self) -> float:
        """Calculate download progress percentage"""
        if not self.total_size or self.total_size == 0:
            return 0.0
        return min(100.0, (self.downloaded_size / self.total_size) * 100.0)
    
    @property
    def is_resumable(self) -> bool:
        """Check if this download can be resumed"""
        return (
            self.status in ['paused', 'failed'] and 
            self.temp_file_path and 
            self.resume_position > 0 and
            self.retry_count < self.max_retries
        )
    
    def get_download_metadata_dict(self) -> dict:
        """Parse download metadata JSON string to dict"""
        if self.download_metadata:
            try:
                return json.loads(self.download_metadata)
            except json.JSONDecodeError:
                return {}
        return {}
    
    def set_download_metadata_dict(self, metadata_dict: dict):
        """Set download metadata from dict"""
        self.download_metadata = json.dumps(metadata_dict) if metadata_dict else None
    
    def can_retry(self) -> bool:
        """Check if download can be retried"""
        return self.retry_count < self.max_retries
    
    def increment_retry(self):
        """Increment retry counter"""
        self.retry_count += 1
        self.updated_at = func.now()
