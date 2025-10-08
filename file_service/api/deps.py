"""Dependency injection for API endpoints."""

from typing import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from types_aiobotocore_s3 import S3Client

from core.database import get_db
from core.s3 import get_s3_client
from services.file_service import FileService


async def get_file_service(
    db_session: AsyncSession = Depends(get_db),
    s3_client: S3Client = Depends(get_s3_client),
) -> FileService:
    """Dependency for file service injection.
    
    Args:
        db_session: Database session from get_db dependency
        s3_client: S3 client from get_s3_client dependency
    
    Returns:
        FileService instance with database session and S3 client
    """
    return FileService(db_session, s3_client)
