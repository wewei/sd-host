#!/usr/bin/env python3
"""
Add test models to database for prefix testing
"""
import asyncio
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from core.database import get_db
from models.entities import Model
from sqlalchemy import text

async def add_test_models():
    """Add test models to database"""
    
    # Test model data
    models = [
        {
            "hash": "abcd1234567890123456789012345678901234567890123456789012345678901234",
            "name": "Disney Princess LoRA v1",
            "model_type": "lora",  # Fixed: lowercase
            "size": 1024
        },
        {
            "hash": "abcdef123456789012345678901234567890123456789012345678901234567890",
            "name": "Disney Princess LoRA v2", 
            "model_type": "lora",  # Fixed: lowercase
            "size": 1024
        },
        {
            "hash": "xyz1234567890123456789012345678901234567890123456789012345678901234",
            "name": "Another Model",
            "model_type": "checkpoint",  # Fixed: lowercase
            "size": 2048
        }
    ]
    
    async for session in get_db():
        try:
            for model_data in models:
                # Check if model already exists
                result = await session.execute(
                    text("SELECT COUNT(*) FROM models WHERE hash = :hash"),
                    {"hash": model_data["hash"]}
                )
                count = result.scalar()
                
                if count == 0:
                    # Add model
                    await session.execute(
                        text("""
                            INSERT INTO models (hash, name, model_type, size, created_at, updated_at)
                            VALUES (:hash, :name, :model_type, :size, datetime('now'), datetime('now'))
                        """),
                        model_data
                    )
                    print(f"Added model: {model_data['name']} ({model_data['hash'][:8]}...)")
                else:
                    print(f"Model already exists: {model_data['name']} ({model_data['hash'][:8]}...)")
            
            await session.commit()
            print("✅ All test models added successfully!")
            
        except Exception as e:
            await session.rollback()
            print(f"❌ Error adding models: {e}")
            raise
        finally:
            await session.close()
            break

if __name__ == "__main__":
    asyncio.run(add_test_models())
