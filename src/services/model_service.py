"""
Model service layer for business logic
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc, asc
from sqlalchemy.orm import selectinload
from typing import List, Optional, Dict, Any, Tuple
import json
import hashlib
import os
from datetime import datetime

from models.entities import Model, ModelTag, Tag, Image
from models.schemas import (
    ModelResource, ModelListResponse, ModelDetailResponse,
    ModelFilters, PaginationParams, SortParams, FieldsParams,
    ModelAttributes, ModelRelationships, TagResource, ImageResource,
    ModelUpdateRequest, ModelBatchUpdateRequest
)


class ModelService:
    """Service class for model operations"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_models(
        self,
        filters: ModelFilters,
        pagination: PaginationParams,
        sort_params: SortParams,
        fields: FieldsParams = None
    ) -> ModelListResponse:
        """Get paginated list of models with filtering and sorting"""
        
        # Build base query
        query = select(Model)
        
        # Apply filters
        query = self._apply_filters(query, filters)
        
        # Apply sorting
        query = self._apply_sorting(query, sort_params)
        
        # Get total count for pagination
        count_query = select(func.count()).select_from(query.subquery())
        total_count = await self.session.scalar(count_query)
        
        # Apply pagination
        offset = (pagination.number - 1) * pagination.size
        query = query.offset(offset).limit(pagination.size)
        
        # Load relationships if needed
        if not fields or not fields.model:
            query = query.options(
                selectinload(Model.tags).selectinload(ModelTag.tag),
                selectinload(Model.cover_image)
            )
        
        # Execute query
        result = await self.session.execute(query)
        models = result.scalars().all()
        
        # Convert to response format
        model_resources = []
        for model in models:
            model_resource = await self._model_to_resource(model, fields)
            model_resources.append(model_resource)
        
        # Build pagination metadata
        total_pages = (total_count + pagination.size - 1) // pagination.size
        meta = {
            "pagination": {
                "page": pagination.number,
                "pages": total_pages,
                "per_page": pagination.size,
                "total": total_count
            }
        }
        
        # Build pagination links
        links = self._build_pagination_links(pagination, total_pages)
        
        return ModelListResponse(
            data=model_resources,
            meta=meta,
            links=links
        )
    
    async def get_model_by_hash(self, model_hash: str) -> Optional[ModelDetailResponse]:
        """Get single model by hash"""
        query = select(Model).where(Model.hash == model_hash).options(
            selectinload(Model.tags).selectinload(ModelTag.tag),
            selectinload(Model.cover_image)
        )
        
        result = await self.session.execute(query)
        model = result.scalar_one_or_none()
        
        if not model:
            return None
        
        model_resource = await self._model_to_resource(model)
        
        # Build included resources
        included = []
        
        # Add tags to included
        for model_tag in model.tags:
            tag_resource = TagResource(id=model_tag.tag.name)
            included.append(tag_resource)
        
        # Add cover image to included if exists
        if model.cover_image:
            image_resource = ImageResource(id=model.cover_image.hash)
            included.append(image_resource)
        
        return ModelDetailResponse(
            data=model_resource,
            included=included if included else None
        )
    
    async def update_model(self, model_hash: str, update_data: ModelUpdateRequest) -> Dict[str, Any]:
        """Update model metadata"""
        query = select(Model).where(Model.hash == model_hash)
        result = await self.session.execute(query)
        model = result.scalar_one_or_none()
        
        if not model:
            return {"success": False, "error": "Model not found"}
        
        updated_fields = []
        
        # Update metadata fields
        metadata = model.get_metadata_dict()
        
        if update_data.tag_high_quality is not None:
            metadata["high_quality"] = update_data.tag_high_quality
            updated_fields.append("tag_high_quality")
        
        if update_data.rating is not None:
            metadata["rating"] = update_data.rating
            updated_fields.append("rating")
        
        if update_data.is_favorite is not None:
            metadata["favorite"] = update_data.is_favorite
            updated_fields.append("is_favorite")
        
        if update_data.custom_note is not None:
            metadata["custom_note"] = update_data.custom_note
            updated_fields.append("custom_note")
        
        # Save metadata
        model.set_metadata_dict(metadata)
        
        # Handle tags
        if update_data.tags is not None:
            await self._update_model_tags(model, update_data.tags)
            updated_fields.append("tags")
        
        model.updated_at = datetime.utcnow()
        
        try:
            await self.session.commit()
            return {
                "success": True,
                "updated_fields": updated_fields
            }
        except Exception as e:
            await self.session.rollback()
            return {
                "success": False,
                "error": str(e)
            }
    
    async def batch_update_models(self, update_data: ModelBatchUpdateRequest) -> Dict[str, Any]:
        """Batch update multiple models"""
        success = []
        failed = []
        
        for model_hash, model_update in update_data.models.items():
            result = await self.update_model(model_hash, model_update)
            if result["success"]:
                success.append(model_hash)
            else:
                failed.append({
                    "hash": model_hash,
                    "error": result.get("error", "Unknown error")
                })
        
        return {
            "success": success,
            "failed": failed
        }
    
    async def delete_model(self, model_hash: str) -> Dict[str, Any]:
        """Delete a single model"""
        query = select(Model).where(Model.hash == model_hash)
        result = await self.session.execute(query)
        model = result.scalar_one_or_none()
        
        if not model:
            return {
                "success": False,
                "message": "Model not found"
            }
        
        # Check if model is in use by active tasks
        # This would require checking Task table - simplified for now
        
        try:
            # Delete model file if exists
            await self._delete_model_file(model_hash)
            
            # Delete from database
            await self.session.delete(model)
            await self.session.commit()
            
            return {
                "success": True,
                "message": "Model deleted successfully"
            }
        except Exception as e:
            await self.session.rollback()
            return {
                "success": False,
                "message": f"Failed to delete model: {str(e)}"
            }
    
    async def batch_delete_models(self, model_hashes: List[str]) -> Dict[str, Any]:
        """Batch delete multiple models"""
        deleted = []
        failed = []
        
        for model_hash in model_hashes:
            result = await self.delete_model(model_hash)
            if result["success"]:
                deleted.append(model_hash)
            else:
                failed.append({
                    "hash": model_hash,
                    "reason": result["message"]
                })
        
        return {
            "deleted": deleted,
            "failed": failed,
            "count": len(deleted)
        }
    
    def _apply_filters(self, query, filters: ModelFilters):
        """Apply filters to query"""
        conditions = []
        
        if filters.model_type:
            conditions.append(Model.model_type == filters.model_type)
        
        if filters.base_model:
            conditions.append(Model.base_model == filters.base_model)
        
        if filters.name_contains:
            conditions.append(Model.name.contains(filters.name_contains))
        
        if filters.size_gte:
            conditions.append(Model.size >= filters.size_gte)
        
        if filters.size_lte:
            conditions.append(Model.size <= filters.size_lte)
        
        if filters.base_model_contains:
            conditions.append(Model.base_model.contains(filters.base_model_contains))
        
        if filters.base_model_in:
            conditions.append(Model.base_model.in_(filters.base_model_in))
        
        # Tag filtering requires joins
        if filters.tags_any or filters.tags_none:
            query = query.join(ModelTag, ModelTag.model_hash == Model.hash)
            query = query.join(Tag, Tag.name == ModelTag.tag_name)
            
            if filters.tags_any:
                conditions.append(Tag.name.in_(filters.tags_any))
            
            if filters.tags_none:
                # Exclude models with these tags
                subquery = select(ModelTag.model_hash).where(
                    ModelTag.tag_name.in_(filters.tags_none)
                )
                conditions.append(~Model.hash.in_(subquery))
        
        if conditions:
            query = query.where(and_(*conditions))
        
        return query
    
    def _apply_sorting(self, query, sort_params: SortParams):
        """Apply sorting to query"""
        sort_field = sort_params.sort
        descending = sort_field.startswith("-")
        
        if descending:
            field_name = sort_field[1:]
        else:
            field_name = sort_field
        
        # Map field names to Model attributes
        field_mapping = {
            "name": Model.name,
            "created_at": Model.created_at,
            "updated_at": Model.updated_at,
            "size": Model.size,
            "model_type": Model.model_type,
        }
        
        if field_name in field_mapping:
            field = field_mapping[field_name]
            if descending:
                query = query.order_by(desc(field))
            else:
                query = query.order_by(asc(field))
        
        return query
    
    async def _model_to_resource(self, model: Model, fields: FieldsParams = None) -> ModelResource:
        """Convert Model entity to ModelResource"""
        # Build attributes
        attributes = ModelAttributes(
            name=model.name,
            model_type=model.model_type,
            base_model=model.base_model,
            size=model.size,
            source_url=model.source_url,
            metadata=model.get_metadata_dict(),
            description=model.description,
            created_at=model.created_at,
            updated_at=model.updated_at
        )
        
        # Build relationships
        relationships = None
        if not fields or not fields.model:
            # Include tags
            tag_resources = []
            for model_tag in model.tags:
                tag_resources.append(TagResource(id=model_tag.tag.name))
            
            # Include cover image
            cover_image = None
            if model.cover_image:
                cover_image = ImageResource(id=model.cover_image.hash)
            
            relationships = ModelRelationships(
                tags={"data": tag_resources},
                cover_image={"data": cover_image}
            )
        
        return ModelResource(
            id=model.hash,
            attributes=attributes,
            relationships=relationships
        )
    
    def _build_pagination_links(self, pagination: PaginationParams, total_pages: int) -> Dict[str, str]:
        """Build pagination links"""
        links = {}
        
        # First page
        links["first"] = f"?page[number]=1&page[size]={pagination.size}"
        
        # Last page
        links["last"] = f"?page[number]={total_pages}&page[size]={pagination.size}"
        
        # Previous page
        if pagination.number > 1:
            links["prev"] = f"?page[number]={pagination.number - 1}&page[size]={pagination.size}"
        
        # Next page
        if pagination.number < total_pages:
            links["next"] = f"?page[number]={pagination.number + 1}&page[size]={pagination.size}"
        
        return links
    
    async def _update_model_tags(self, model: Model, tag_names: List[str]):
        """Update model tags"""
        # Remove existing tags
        for model_tag in model.tags:
            await self.session.delete(model_tag)
        
        # Add new tags
        for tag_name in tag_names:
            # Ensure tag exists
            tag_query = select(Tag).where(Tag.name == tag_name)
            tag_result = await self.session.execute(tag_query)
            tag = tag_result.scalar_one_or_none()
            
            if not tag:
                tag = Tag(name=tag_name)
                self.session.add(tag)
                await self.session.flush()
            
            # Create model-tag association
            model_tag = ModelTag(model_hash=model.hash, tag_name=tag_name)
            self.session.add(model_tag)
    
    async def _delete_model_file(self, model_hash: str):
        """Delete model file from filesystem"""
        # This is a placeholder - implement actual file deletion logic
        model_path = f"./models/{model_hash}.safetensors"
        if os.path.exists(model_path):
            os.remove(model_path)
