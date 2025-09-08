"""
Model action API routes - for operations like downloading from Civitai
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import json

from core.database import get_db
from services.civitai_service import CivitaiService
from models.schemas import (
    CivitaiAddRequest, CivitaiAddResponse, ErrorResponse, ErrorDetail
)


router = APIRouter(prefix="/api/model-actions", tags=["model-actions"])


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


@router.get("/add-from-civitai/{model_hash}")
async def track_civitai_download(
    model_hash: str,
    db: AsyncSession = Depends(get_db)
):
    """SSE endpoint for tracking Civitai download progress."""
    try:
        civitai_service = CivitaiService(db)
        
        async def generate():
            async for progress_data in civitai_service.get_download_progress(model_hash):
                yield f"data: {json.dumps(progress_data)}\n\n"
        
        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            }
        )
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail="Download not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/validate-civitai-url")
async def validate_civitai_url(
    url: str,
    db: AsyncSession = Depends(get_db)
):
    """Validate and extract information from a Civitai URL."""
    try:
        civitai_service = CivitaiService(db)
        # 这里可以添加URL解析逻辑
        # 例如从 https://civitai.com/models/212532?modelVersionId=244808 解析模型ID
        return {"valid": True, "model_id": "212532", "version_id": "244808"}
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/download-status/{model_hash}")
async def get_download_status(
    model_hash: str,
    db: AsyncSession = Depends(get_db)
):
    """Get current download status for a model."""
    try:
        civitai_service = CivitaiService(db)
        status = await civitai_service.get_download_status(model_hash)
        return status
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail="Download not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")
