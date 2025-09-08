"""
Model API routes
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import StreamingResponse, FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
import os

from core.database import get_db
from services.model_service import ModelService
from services.civitai_service import CivitaiService
from models.schemas import (
    ModelListResponse, ModelDetailResponse, ModelFilters, PaginationParams, 
    SortParams, FieldsParams, ModelUpdateRequest, ModelBatchUpdateRequest,
    ModelDeleteRequest, CivitaiAddRequest, ModelUpdateResponse,
    ModelBatchUpdateResponse, ModelDeleteResponse, ModelBatchDeleteResponse,
    CivitaiAddResponse, ErrorResponse, ErrorDetail
)


router = APIRouter(prefix="/api/models", tags=["models"])


@router.get("", response_model=ModelListResponse)
async def get_models(
    # Filters
    model_type: Optional[str] = Query(None, alias="filter[model_type]"),
    base_model: Optional[str] = Query(None, alias="filter[base_model]"),
    name_contains: Optional[str] = Query(None, alias="filter[name][contains]"),
    size_gte: Optional[int] = Query(None, alias="filter[size][gte]"),
    size_lte: Optional[int] = Query(None, alias="filter[size][lte]"),
    tags_any: Optional[str] = Query(None, alias="filter[tags][any]"),
    tags_none: Optional[str] = Query(None, alias="filter[tags][none]"),
    base_model_in: Optional[str] = Query(None, alias="filter[base_model][in]"),
    base_model_contains: Optional[str] = Query(None, alias="filter[base_model][contains]"),
    
    # Pagination
    page_number: int = Query(1, alias="page[number]", ge=1),
    page_size: int = Query(50, alias="page[size]", ge=1, le=200),
    
    # Sorting
    sort: str = Query("-created_at"),
    
    # Field selection
    fields_model: Optional[str] = Query(None, alias="fields[model]"),
    
    # Include
    include: Optional[str] = Query(None),
    
    db: AsyncSession = Depends(get_db)
):
    """
    Get paginated list of models with filtering and sorting.
    
    Supports JSON API standard query parameters:
    - Filtering: filter[field]=value, filter[field][operator]=value
    - Pagination: page[number], page[size]
    - Sorting: sort (prefix with - for descending)
    - Field selection: fields[model]
    - Include: include related resources
    """
    try:
        # Build filter object
        filters = ModelFilters(
            model_type=model_type,
            base_model=base_model,
            name_contains=name_contains,
            size_gte=size_gte,
            size_lte=size_lte,
            tags_any=tags_any,
            tags_none=tags_none,
            base_model_in=base_model_in,
            base_model_contains=base_model_contains
        )
        
        # Build pagination object
        pagination = PaginationParams(number=page_number, size=page_size)
        
        # Build sort object
        sort_params = SortParams(sort=sort)
        
        # Build fields object
        fields = FieldsParams(model=fields_model) if fields_model else None
        
        # Get models
        model_service = ModelService(db)
        result = await model_service.get_models(filters, pagination, sort_params, fields)
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{model_hash}", response_model=ModelDetailResponse)
async def get_model(
    model_hash: str,
    include: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Get single model by hash with optional included resources."""
    try:
        model_service = ModelService(db)
        result = await model_service.get_model_by_hash(model_hash)
        
        if not result:
            raise HTTPException(status_code=404, detail="Model not found")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{model_hash}/content")
async def get_model_content(
    model_hash: str,
    db: AsyncSession = Depends(get_db)
):
    """Download model file content directly."""
    try:
        # Check if model exists
        model_service = ModelService(db)
        model_response = await model_service.get_model_by_hash(model_hash)
        
        if not model_response:
            raise HTTPException(status_code=404, detail="Model not found")
        
        # Check if file exists
        model_path = f"./models/{model_hash}.safetensors"
        if not os.path.exists(model_path):
            raise HTTPException(status_code=404, detail="Model file not found")
        
        # Return file
        model_name = model_response.data.attributes.name
        filename = f"{model_name}.safetensors"
        
        return FileResponse(
            path=model_path,
            media_type="application/octet-stream",
            filename=filename
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{model_hash}", response_model=ModelUpdateResponse)
async def update_model(
    model_hash: str,
    update_data: ModelUpdateRequest,
    db: AsyncSession = Depends(get_db)
):
    """Update model metadata."""
    try:
        model_service = ModelService(db)
        result = await model_service.update_model(model_hash, update_data)
        
        if not result["success"]:
            if "not found" in result.get("error", "").lower():
                raise HTTPException(status_code=404, detail=result["error"])
            else:
                raise HTTPException(status_code=400, detail=result["error"])
        
        return ModelUpdateResponse(
            success=True,
            updated_fields=result["updated_fields"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("", response_model=ModelBatchUpdateResponse)
async def batch_update_models(
    update_data: ModelBatchUpdateRequest,
    db: AsyncSession = Depends(get_db)
):
    """Batch update multiple models."""
    try:
        model_service = ModelService(db)
        result = await model_service.batch_update_models(update_data)
        
        return ModelBatchUpdateResponse(
            success=result["success"],
            failed=result["failed"]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/{model_hash}", response_model=ModelDeleteResponse)
async def delete_model(
    model_hash: str,
    db: AsyncSession = Depends(get_db)
):
    """Delete a single model."""
    try:
        model_service = ModelService(db)
        result = await model_service.delete_model(model_hash)
        
        if not result["success"]:
            if "not found" in result["message"].lower():
                raise HTTPException(status_code=404, detail=result["message"])
            else:
                raise HTTPException(status_code=400, detail=result["message"])
        
        return ModelDeleteResponse(
            success=True,
            message=result["message"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("", response_model=ModelBatchDeleteResponse)
async def batch_delete_models(
    delete_data: ModelDeleteRequest,
    db: AsyncSession = Depends(get_db)
):
    """Batch delete multiple models."""
    try:
        model_service = ModelService(db)
        result = await model_service.batch_delete_models(delete_data.hashes)
        
        return ModelBatchDeleteResponse(
            deleted=result["deleted"],
            failed=result["failed"],
            count=result["count"]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/add-from-civitai", response_model=CivitaiAddResponse)
async def add_model_from_civitai(
    request: CivitaiAddRequest,
    db: AsyncSession = Depends(get_db)
):
    """Add a new model from Civitai."""
    try:
        civitai_service = CivitaiService(db)
        result = await civitai_service.add_model_from_civitai(
            request.model_id, 
            request.version_id
        )
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")
    
    # try:
    #     civitai_service = CivitaiService(db)
    #     print(f"[DEBUG] Created CivitaiService")
    #     result = await civitai_service.add_model_from_civitai(
    #         request.model_id, 
    #         request.version_id
    #     )
    #     print(f"[DEBUG] Service returned: {result}")
    #     
    #     return result
    #     
    # except ValueError as e:
    #     print(f"[DEBUG] ValueError: {e}")
    #     raise HTTPException(status_code=400, detail=str(e))
    # except Exception as e:
    #     print(f"[DEBUG] Exception: {e}")
    #     import traceback
    #     traceback.print_exc()
    #     raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/add-from-civitai/{model_hash}")
async def track_civitai_download(
    model_hash: str,
    db: AsyncSession = Depends(get_db)
):
    """SSE endpoint for tracking Civitai download progress."""
    try:
        civitai_service = CivitaiService(db)
        
        async def generate():
            async for data in civitai_service.get_download_progress(model_hash):
                yield data
        
        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Cache-Control"
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")
