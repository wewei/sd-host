#!/usr/bin/env python3
"""
Fix updated_at field for existing models
"""
import asyncio
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from core.database import get_db
from sqlalchemy import text

async def fix_updated_at():
    """Fix updated_at field for all models"""
    async for session in get_db():
        try:
            # Update all models to have updated_at = created_at where updated_at is NULL
            result = await session.execute(
                text("""
                    UPDATE models 
                    SET updated_at = created_at 
                    WHERE updated_at IS NULL
                """)
            )
            
            await session.commit()
            print(f"✅ Fixed updated_at for {result.rowcount} models")
            
        except Exception as e:
            await session.rollback()
            print(f"❌ Error fixing updated_at: {e}")
            raise
        finally:
            await session.close()
            break

if __name__ == "__main__":
    asyncio.run(fix_updated_at())
