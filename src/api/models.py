"""
Model API routes
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import StreamingResponse, FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
import os
import json

from core.database import get_db
from services.model_service import ModelService
from services.civitai_service import CivitaiService
from models.schemas import (
    ModelListResponse, ModelDetailResponse, ModelFilters, PaginationParams, 
    SortParams, FieldsParams, ModelUpdateRequest, ModelBatchUpdateRequest,
    ModelDeleteRequest, ModelUpdateResponse,
    ModelBatchUpdateResponse, ModelDeleteResponse, ModelBatchDeleteResponse,
    CivitaiAddRequest, CivitaiAddResponse,
    ModelTagRequest, ModelTagResponse, ModelTagOperationResult,
    DownloadTaskListResponse, DownloadTaskDetailResponse, DownloadTaskResource,
    DownloadTaskActionRequest, DownloadTaskActionResponse,
    DownloadTaskBatchActionRequest, DownloadTaskBatchActionResponse,
    ErrorResponse, ErrorDetail
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


# ==================== Download Task Management Endpoints ====================
# Note: These routes must come BEFORE /{model_hash} to avoid conflicts

@router.get("/download-tasks", response_model=DownloadTaskListResponse)
async def list_download_tasks(
    db: AsyncSession = Depends(get_db)
):
    """Get all download tasks with their current status"""
    try:
        civitai_service = CivitaiService(db)
        await civitai_service.initialize_from_database()
        tasks = await civitai_service.get_all_download_tasks()
        
        task_resources = [
            DownloadTaskResource(
                hash=task["hash"],
                status=task["status"],
                progress=task["progress"],
                speed=task["speed"],
                eta=task["eta"],
                model_name=task["model_name"],
                version_name=task["version_name"],
                size=task["size"],
                downloaded=task["downloaded"],
                created_at=task["created_at"],
                error=task["error"]
            )
            for task in tasks
        ]
        
        return DownloadTaskListResponse(
            data=task_resources,
            meta={"count": len(task_resources)}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/download-tasks/{task_hash}", response_model=DownloadTaskDetailResponse)
async def get_download_task(
    task_hash: str,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific download task by hash"""
    try:
        civitai_service = CivitaiService(db)
        await civitai_service.initialize_from_database()
        task = await civitai_service.get_download_task(task_hash)
        
        if not task:
            raise HTTPException(status_code=404, detail="Download task not found")
        
        task_resource = DownloadTaskResource(
            hash=task["hash"],
            status=task["status"],
            progress=task["progress"],
            speed=task["speed"],
            eta=task["eta"],
            model_name=task["model_name"],
            version_name=task["version_name"],
            size=task["size"],
            downloaded=task["downloaded"],
            created_at=task["created_at"],
            error=task["error"]
        )
        
        return DownloadTaskDetailResponse(data=task_resource)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/download-tasks/{task_hash}/action", response_model=DownloadTaskActionResponse)
async def control_download_task(
    task_hash: str,
    request: DownloadTaskActionRequest,
    db: AsyncSession = Depends(get_db)
):
    """Perform action on a download task (pause, resume, cancel, remove)"""
    try:
        civitai_service = CivitaiService(db)
        await civitai_service.initialize_from_database()
        action = request.action.lower()
        
        success = False
        message = ""
        
        if action == "pause":
            success = await civitai_service.pause_download_task(task_hash)
            message = "Download paused" if success else "Failed to pause download"
        elif action == "resume":
            success = await civitai_service.resume_download_task(task_hash)
            message = "Download resumed" if success else "Failed to resume download"
        elif action == "cancel":
            success = await civitai_service.cancel_download_task(task_hash)
            message = "Download cancelled" if success else "Failed to cancel download"
        elif action == "remove":
            success = await civitai_service.remove_download_task(task_hash)
            message = "Task removed" if success else "Failed to remove task"
        else:
            raise HTTPException(status_code=400, detail="Invalid action. Use: pause, resume, cancel, or remove")
        
        if not success:
            raise HTTPException(status_code=400, detail=message)
        
        # Get updated task info
        task = await civitai_service.get_download_task(task_hash)
        task_resource = None
        if task:
            task_resource = DownloadTaskResource(
                hash=task["hash"],
                status=task["status"],
                progress=task["progress"],
                speed=task["speed"],
                eta=task["eta"],
                model_name=task["model_name"],
                version_name=task["version_name"],
                size=task["size"],
                downloaded=task["downloaded"],
                created_at=task["created_at"],
                error=task["error"]
            )
        
        return DownloadTaskActionResponse(
            success=True,
            message=message,
            data=task_resource
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/download-tasks/batch-action", response_model=DownloadTaskBatchActionResponse)
async def batch_control_download_tasks(
    request: DownloadTaskBatchActionRequest,
    db: AsyncSession = Depends(get_db)
):
    """Perform batch action on multiple download tasks"""
    try:
        civitai_service = CivitaiService(db)
        await civitai_service.initialize_from_database()
        action = request.action.lower()
        results = []
        
        for task_hash in request.task_hashes:
            try:
                success = False
                message = ""
                
                if action == "pause":
                    success = civitai_service.pause_download_task(task_hash)
                    message = "Download paused" if success else "Failed to pause download"
                elif action == "resume":
                    success = civitai_service.resume_download_task(task_hash)
                    message = "Download resumed" if success else "Failed to resume download"
                elif action == "cancel":
                    success = civitai_service.cancel_download_task(task_hash)
                    message = "Download cancelled" if success else "Failed to cancel download"
                elif action == "remove":
                    success = civitai_service.remove_download_task(task_hash)
                    message = "Task removed" if success else "Failed to remove task"
                else:
                    success = False
                    message = "Invalid action"
                
                results.append({
                    "hash": task_hash,
                    "success": success,
                    "message": message
                })
                
            except Exception as e:
                results.append({
                    "hash": task_hash,
                    "success": False,
                    "message": str(e)
                })
        
        overall_success = all(result["success"] for result in results)
        successful_count = sum(1 for result in results if result["success"])
        
        return DownloadTaskBatchActionResponse(
            success=overall_success,
            message=f"Processed {successful_count}/{len(results)} tasks successfully",
            results=results
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/download-tasks/completed")
async def clear_completed_download_tasks(
    db: AsyncSession = Depends(get_db)
):
    """Remove all completed, failed, and cancelled download tasks"""
    try:
        civitai_service = CivitaiService(db)
        await civitai_service.initialize_from_database()
        removed_count = await civitai_service.clear_completed_tasks()
        
        return {
            "success": True,
            "message": f"Removed {removed_count} completed tasks",
            "count": removed_count
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/download-tasks/mock")
async def create_mock_download_task(
    db: AsyncSession = Depends(get_db),
    model_name: str = "Test Model",
    version_name: str = "v1.0"
):
    """Create a mock download task for testing purposes"""
    try:
        civitai_service = CivitaiService(db)
        await civitai_service.initialize_from_database()
        task_hash = await civitai_service.create_mock_download_task(model_name, version_name)
        
        return {
            "success": True,
            "message": "Mock download task created",
            "hash": task_hash
        }
        
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
        from core.config import get_settings
        settings = get_settings()
        model_path = os.path.join(settings.models_dir, f"{model_hash}.safetensors")
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





@router.post("/batch-update", response_model=ModelBatchUpdateResponse)
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
                yield progress_data
        
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


@router.post("/tag", response_model=ModelTagResponse)
async def tag_models(
    request: ModelTagRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Add tags to models.
    
    Accepts a list of operations, where each operation contains:
    - entities: List of model hashes
    - tags: List of tag names
    
    Creates tag relationships for the Cartesian product of entities × tags.
    """
    try:
        model_service = ModelService(db)
        
        # Extract operations from request
        operations = request.root
        
        total_operations = 0
        successful_operations = 0
        failed_operations = 0
        results = []
        
        # Process each operation
        for operation in operations:
            # Create Cartesian product
            for entity_hash in operation.entities:
                for tag_name in operation.tags:
                    total_operations += 1
                    
                    try:
                        # Add tag to model
                        success = await model_service.add_tag_to_model(entity_hash, tag_name)
                        
                        if success:
                            successful_operations += 1
                            results.append(ModelTagOperationResult(
                                entity=entity_hash,
                                tag=tag_name,
                                success=True
                            ))
                        else:
                            failed_operations += 1
                            results.append(ModelTagOperationResult(
                                entity=entity_hash,
                                tag=tag_name,
                                success=False,
                                message="Model not found"
                            ))
                            
                    except Exception as e:
                        failed_operations += 1
                        results.append(ModelTagOperationResult(
                            entity=entity_hash,
                            tag=tag_name,
                            success=False,
                            message=str(e)
                        ))
        
        # Determine overall success
        overall_success = failed_operations == 0
        message = f"Tagged {successful_operations}/{total_operations} model-tag pairs"
        
        return ModelTagResponse(
            success=overall_success,
            message=message,
            total_operations=total_operations,
            successful_operations=successful_operations,
            failed_operations=failed_operations,
            results=results
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/untag", response_model=ModelTagResponse)
async def untag_models(
    request: ModelTagRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Remove tags from models.
    
    Accepts a list of operations, where each operation contains:
    - entities: List of model hashes
    - tags: List of tag names
    
    Removes tag relationships for the Cartesian product of entities × tags.
    """
    try:
        model_service = ModelService(db)
        
        # Extract operations from request
        operations = request.root
        
        total_operations = 0
        successful_operations = 0
        failed_operations = 0
        results = []
        
        # Process each operation
        for operation in operations:
            # Create Cartesian product
            for entity_hash in operation.entities:
                for tag_name in operation.tags:
                    total_operations += 1
                    
                    try:
                        # Remove tag from model
                        success = await model_service.remove_tag_from_model(entity_hash, tag_name)
                        
                        if success:
                            successful_operations += 1
                            results.append(ModelTagOperationResult(
                                entity=entity_hash,
                                tag=tag_name,
                                success=True
                            ))
                        else:
                            failed_operations += 1
                            results.append(ModelTagOperationResult(
                                entity=entity_hash,
                                tag=tag_name,
                                success=False,
                                message="Model or tag relationship not found"
                            ))
                            
                    except Exception as e:
                        failed_operations += 1
                        results.append(ModelTagOperationResult(
                            entity=entity_hash,
                            tag=tag_name,
                            success=False,
                            message=str(e)
                        ))
        
        # Determine overall success
        overall_success = failed_operations == 0
        message = f"Untagged {successful_operations}/{total_operations} model-tag pairs"
        
        return ModelTagResponse(
            success=overall_success,
            message=message,
            total_operations=total_operations,
            successful_operations=successful_operations,
            failed_operations=failed_operations,
            results=results
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")
