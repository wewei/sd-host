"""
Pydantic schemas for API request/response validation
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum


class ModelType(str, Enum):
    """Supported model types"""
    CHECKPOINT = "checkpoint"
    LORA = "lora"
    CONTROLNET = "controlnet"
    VAE = "vae"
    EMBEDDING = "embedding"


class ModelStatus(str, Enum):
    """Model status values"""
    READY = "ready"
    DOWNLOADING = "downloading"
    ERROR = "error"


class BaseModelType(str, Enum):
    """Base model architectures"""
    SD1_5 = "SD1.5"
    SDXL = "SDXL"
    SD2 = "SD2"
    OTHER = "other"


# JSON API Resource schemas
class TagResource(BaseModel):
    """Tag resource representation"""
    type: str = "tag"
    id: str
    
    class Config:
        from_attributes = True


class ImageResource(BaseModel):
    """Image resource representation"""
    type: str = "image"
    id: str  # hash
    
    class Config:
        from_attributes = True


class ModelAttributes(BaseModel):
    """Model attributes for JSON API response"""
    name: str
    model_type: ModelType
    base_model: Optional[str] = None
    size: int
    source_url: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    description: Optional[str] = None
    status: ModelStatus = ModelStatus.READY
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ModelRelationships(BaseModel):
    """Model relationships for JSON API response"""
    tags: Dict[str, List[TagResource]] = {"data": []}
    cover_image: Dict[str, Optional[ImageResource]] = {"data": None}
    
    class Config:
        from_attributes = True


class ModelResource(BaseModel):
    """Complete model resource for JSON API response"""
    type: str = "model"
    id: str  # hash
    attributes: ModelAttributes
    relationships: Optional[ModelRelationships] = None
    
    class Config:
        from_attributes = True


class ModelListResponse(BaseModel):
    """Model list response following JSON API specification"""
    data: List[ModelResource]
    meta: Dict[str, Any] = {}
    links: Dict[str, Any] = {}
    
    class Config:
        from_attributes = True


class ModelDetailResponse(BaseModel):
    """Single model response following JSON API specification"""
    data: ModelResource
    included: Optional[List[Union[TagResource, ImageResource]]] = None
    
    class Config:
        from_attributes = True


# Filter schemas for query parsing
class ModelFilters(BaseModel):
    """Model filtering parameters"""
    model_type: Optional[ModelType] = None
    base_model: Optional[str] = None
    name_contains: Optional[str] = Field(None, alias="name[contains]")
    size_gte: Optional[int] = Field(None, alias="size[gte]")
    size_lte: Optional[int] = Field(None, alias="size[lte]")
    tags_any: Optional[str] = Field(None, alias="tags[any]")  # Comma-separated
    tags_none: Optional[str] = Field(None, alias="tags[none]")  # Comma-separated
    base_model_in: Optional[str] = Field(None, alias="base_model[in]")  # Comma-separated
    base_model_contains: Optional[str] = Field(None, alias="base_model[contains]")
    
    @validator("tags_any", "tags_none", "base_model_in", pre=True)
    def parse_comma_separated(cls, v):
        """Parse comma-separated values into lists"""
        if v is None:
            return None
        if isinstance(v, str):
            return [tag.strip() for tag in v.split(",") if tag.strip()]
        return v
    
    class Config:
        populate_by_name = True


class PaginationParams(BaseModel):
    """Pagination parameters following JSON API specification"""
    number: int = Field(1, alias="page[number]", ge=1)
    size: int = Field(50, alias="page[size]", ge=1, le=200)
    
    class Config:
        populate_by_name = True


class SortParams(BaseModel):
    """Sort parameters"""
    sort: str = "-created_at"  # Default: newest first
    
    @validator("sort")
    def validate_sort(cls, v):
        """Validate sort parameter"""
        allowed_fields = ["name", "created_at", "updated_at", "size", "model_type"]
        if v.startswith("-"):
            field = v[1:]
        else:
            field = v
        
        if field not in allowed_fields:
            raise ValueError(f"Invalid sort field: {field}. Allowed: {allowed_fields}")
        return v


class FieldsParams(BaseModel):
    """Fields selection parameters"""
    model: Optional[str] = Field(None, alias="fields[model]")
    
    @validator("model", pre=True)
    def parse_fields(cls, v):
        """Parse comma-separated fields"""
        if v is None:
            return None
        if isinstance(v, str):
            return [field.strip() for field in v.split(",") if field.strip()]
        return v
    
    class Config:
        populate_by_name = True


# Request schemas
class ModelUpdateRequest(BaseModel):
    """Request schema for updating model metadata"""
    tag_high_quality: Optional[bool] = None
    rating: Optional[float] = Field(None, ge=0.0, le=5.0)
    is_favorite: Optional[bool] = None
    custom_note: Optional[str] = None
    tags: Optional[List[str]] = None  # Add/remove tags


class ModelBatchUpdateRequest(BaseModel):
    """Request schema for batch updating models"""
    models: Dict[str, ModelUpdateRequest]  # hash -> update data


class ModelDeleteRequest(BaseModel):
    """Request schema for batch deleting models"""
    hashes: List[str] = Field(..., min_items=1)


class CivitaiAddRequest(BaseModel):
    """Request schema for adding model from Civitai"""
    model_id: str
    version_id: str


# Response schemas
class ModelUpdateResponse(BaseModel):
    """Response schema for model update"""
    success: bool
    updated_fields: List[str] = []
    errors: Optional[Dict[str, str]] = None


class ModelBatchUpdateResponse(BaseModel):
    """Response schema for batch model update"""
    success: List[str] = []  # Successfully updated hashes
    failed: List[Dict[str, str]] = []  # Failed updates with errors


class ModelDeleteResponse(BaseModel):
    """Response schema for model deletion"""
    success: bool
    message: str


class ModelBatchDeleteResponse(BaseModel):
    """Response schema for batch model deletion"""
    deleted: List[str] = []  # Successfully deleted hashes
    failed: List[Dict[str, str]] = []  # Failed deletions with reasons
    count: int


class CivitaiAddResponse(BaseModel):
    """Response schema for Civitai model addition"""
    hash: str
    status: str = "downloading"
    tracking_url: str


class DownloadProgressData(BaseModel):
    """SSE data for download progress"""
    status: str
    progress: Optional[float] = None  # Percentage
    speed: Optional[str] = None
    eta: Optional[str] = None
    model_info: Optional[ModelResource] = None
    error: Optional[str] = None


# Error schemas
class ErrorDetail(BaseModel):
    """JSON API error detail"""
    status: str
    title: str
    detail: Optional[str] = None
    source: Optional[Dict[str, str]] = None


class ErrorResponse(BaseModel):
    """JSON API error response"""
    errors: List[ErrorDetail]


# Download Task Management Schemas
class DownloadTaskResource(BaseModel):
    """Download task resource representation"""
    type: str = "download_task"
    hash: str
    status: str
    progress: float = 0.0
    speed: str = "0 B/s"
    eta: str = "calculating..."
    model_name: str = "Unknown"
    version_name: str = "Unknown"
    size: int = 0
    downloaded: int = 0
    created_at: Optional[str] = None
    error: Optional[str] = None
    
    class Config:
        from_attributes = True


class DownloadTaskListResponse(BaseModel):
    """Response schema for download task list"""
    data: List[DownloadTaskResource]
    meta: Dict[str, Any] = {}


class DownloadTaskDetailResponse(BaseModel):
    """Response schema for single download task"""
    data: DownloadTaskResource


class DownloadTaskActionRequest(BaseModel):
    """Request schema for download task actions"""
    action: str  # pause, resume, cancel, remove


class DownloadTaskActionResponse(BaseModel):
    """Response schema for download task actions"""
    success: bool
    message: str
    data: Optional[DownloadTaskResource] = None


class DownloadTaskBatchActionRequest(BaseModel):
    """Request schema for batch download task actions"""
    task_hashes: List[str]
    action: str  # pause, resume, cancel, remove


class DownloadTaskBatchActionResponse(BaseModel):
    """Response schema for batch download task actions"""
    success: bool
    message: str
    results: List[Dict[str, Any]]  # [{hash: str, success: bool, message: str}]
