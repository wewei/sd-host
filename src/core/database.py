"""
Database configuration and session management
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from typing import AsyncGenerator
import aiosqlite
import os


class Base(DeclarativeBase):
    """Base class for all database models"""
    pass


class DatabaseManager:
    """Database manager for handling SQLite connections"""
    
    def __init__(self, database_url: str = None):
        if database_url is None:
            # Default database path
            database_url = "sqlite+aiosqlite:///./data/sd_host.db"
        
        self.engine = create_async_engine(
            database_url,
            echo=False,  # Set to True for SQL debugging
        )
        self.async_session = async_sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
    
    async def create_tables(self):
        """Create all tables in the database"""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    
    async def close(self):
        """Close database connections"""
        await self.engine.dispose()
    
    def get_session(self) -> AsyncSession:
        """Get a new database session"""
        return self.async_session()


# Global database manager instance
db_manager = DatabaseManager()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for getting database session"""
    async with db_manager.get_session() as session:
        try:
            yield session
        finally:
            await session.close()
