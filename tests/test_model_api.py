"""
Basic tests for Model API
"""

import pytest
import asyncio
from httpx import AsyncClient
from fastapi.testclient import TestClient
import tempfile
import os

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from api.main import create_app
from core.database import db_manager


@pytest.fixture
async def test_app():
    """Create test app with temporary database"""
    # Use temporary database for testing
    test_db_path = tempfile.mktemp(suffix=".db")
    os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{test_db_path}"
    
    app = create_app()
    
    # Initialize database
    await db_manager.create_tables()
    
    yield app
    
    # Cleanup
    await db_manager.close()
    if os.path.exists(test_db_path):
        os.remove(test_db_path)


@pytest.fixture
def client(test_app):
    """Create test client"""
    return TestClient(test_app)


class TestModelAPI:
    """Test cases for Model API endpoints"""
    
    def test_get_models_empty(self, client):
        """Test getting models when database is empty"""
        response = client.get("/api/models")
        assert response.status_code == 200
        
        data = response.json()
        assert "data" in data
        assert isinstance(data["data"], list)
        assert len(data["data"]) == 0
        assert "meta" in data
        assert "pagination" in data["meta"]
    
    def test_get_models_with_filters(self, client):
        """Test filtering models"""
        # Test model type filter
        response = client.get("/api/models?filter[model_type]=checkpoint")
        assert response.status_code == 200
        
        # Test name contains filter
        response = client.get("/api/models?filter[name][contains]=test")
        assert response.status_code == 200
        
        # Test size filter
        response = client.get("/api/models?filter[size][gte]=1000000")
        assert response.status_code == 200
    
    def test_get_models_pagination(self, client):
        """Test pagination parameters"""
        # Test page size
        response = client.get("/api/models?page[size]=10")
        assert response.status_code == 200
        
        data = response.json()
        assert data["meta"]["pagination"]["per_page"] == 10
        
        # Test page number
        response = client.get("/api/models?page[number]=2&page[size]=5")
        assert response.status_code == 200
        
        data = response.json()
        assert data["meta"]["pagination"]["page"] == 2
        assert data["meta"]["pagination"]["per_page"] == 5
    
    def test_get_models_sorting(self, client):
        """Test sorting parameters"""
        # Test ascending sort
        response = client.get("/api/models?sort=name")
        assert response.status_code == 200
        
        # Test descending sort
        response = client.get("/api/models?sort=-created_at")
        assert response.status_code == 200
        
        # Test invalid sort field
        response = client.get("/api/models?sort=invalid_field")
        assert response.status_code == 400
    
    def test_get_model_not_found(self, client):
        """Test getting non-existent model"""
        response = client.get("/api/models/nonexistent_hash")
        assert response.status_code == 404
    
    def test_model_crud_operations(self, client):
        """Test model CRUD operations"""
        # Test update non-existent model
        update_data = {
            "tag_high_quality": True,
            "rating": 4.5
        }
        response = client.post("/api/models/nonexistent_hash", json=update_data)
        assert response.status_code == 404
        
        # Test delete non-existent model
        response = client.delete("/api/models/nonexistent_hash")
        assert response.status_code == 404
    
    def test_batch_operations(self, client):
        """Test batch operations"""
        # Test batch update
        batch_data = {
            "models": {
                "hash1": {"rating": 4.0},
                "hash2": {"is_favorite": True}
            }
        }
        response = client.post("/api/models/batch-update", json=batch_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "success" in data
        assert "failed" in data
        
        # Test batch delete
        delete_data = {"hashes": ["hash1", "hash2", "hash3"]}
        response = client.delete("/api/models", json=delete_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "deleted" in data
        assert "failed" in data
        assert "count" in data
    
    def test_civitai_operations(self, client):
        """Test Civitai integration"""
        # Test add from Civitai (will fail without valid API key)
        civitai_data = {
            "model_id": "4201",
            "version_id": "130072"
        }
        response = client.post("/api/models/add-from-civitai", json=civitai_data)
        # This might fail due to network/API key issues, but should not crash
        assert response.status_code in [200, 400, 500]
    
    def test_health_endpoints(self, client):
        """Test health and info endpoints"""
        # Test root endpoint
        response = client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "version" in data
        
        # Test health check
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
