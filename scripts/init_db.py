"""
Database initialization and migration script
"""

import asyncio
import sys
import os

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.database import db_manager
from models.entities import Tag


async def init_database():
    """Initialize database with tables and default data"""
    print("Initializing database...")
    
    # Create tables
    await db_manager.create_tables()
    print("✓ Database tables created")
    
    # Create default tags
    await create_default_tags()
    print("✓ Default tags created")
    
    print("Database initialization completed!")


async def create_default_tags():
    """Create default tags for models"""
    default_tags = [
        # Style tags
        ("photorealistic", "Photorealistic style models"),
        ("anime", "Anime style models"),
        ("cartoon", "Cartoon style models"),
        ("artistic", "Artistic style models"),
        ("stylized", "Stylized models"),
        
        # Content tags
        ("portrait", "Portrait generation models"),
        ("landscape", "Landscape generation models"),
        ("character", "Character generation models"),
        ("object", "Object generation models"),
        ("architecture", "Architecture generation models"),
        
        # Quality tags
        ("high-quality", "High quality models"),
        ("detailed", "Detailed output models"),
        ("professional", "Professional grade models"),
        ("masterpiece", "Masterpiece quality models"),
        
        # Restriction tags
        ("nsfw", "Not safe for work content"),
        ("adult", "Adult content"),
        ("violence", "Violent content"),
        ("explicit", "Explicit content"),
        
        # Base model tags
        ("sd1.5", "Stable Diffusion 1.5 based"),
        ("sdxl", "Stable Diffusion XL based"),
        ("sd2", "Stable Diffusion 2 based"),
        
        # Model type tags
        ("checkpoint", "Checkpoint models"),
        ("lora", "LoRA models"),
        ("controlnet", "ControlNet models"),
        ("vae", "VAE models"),
        ("embedding", "Embedding models"),
        
        # Usage tags
        ("commercial", "Commercial use allowed"),
        ("non-commercial", "Non-commercial use only"),
        ("favorite", "User favorite models"),
    ]
    
    async with db_manager.get_session() as session:
        try:
            for tag_name, description in default_tags:
                # Check if tag already exists
                from sqlalchemy import select
                query = select(Tag).where(Tag.name == tag_name)
                result = await session.execute(query)
                existing_tag = result.scalar_one_or_none()
                
                if not existing_tag:
                    tag = Tag(name=tag_name, description=description)
                    session.add(tag)
            
            await session.commit()
            print(f"✓ Created {len(default_tags)} default tags")
            
        except Exception as e:
            await session.rollback()
            print(f"✗ Error creating default tags: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(init_database())
