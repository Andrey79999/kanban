"""S3/MinIO client configuration.

This module provides async S3 client setup for file storage operations.
"""

from typing import AsyncGenerator

from aiobotocore.session import get_session
from types_aiobotocore_s3 import S3Client

from .config import settings


async def get_s3_client() -> AsyncGenerator[S3Client, None]:
    """Get async S3 client for MinIO/S3 operations.
    
    Yields:
        S3Client: Configured async S3 client
        
    Example:
        ```python
        async for s3_client in get_s3_client():
            await s3_client.put_object(...)
        ```
    """
    session = get_session()
    
    async with session.create_client(
        's3',
        endpoint_url=f"http{'s' if settings.minio_secure else ''}://{settings.minio_endpoint}",
        aws_access_key_id=settings.minio_access_key,
        aws_secret_access_key=settings.minio_secret_key,
        region_name='us-east-1',
    ) as client:
        yield client


async def ensure_bucket_exists(client: S3Client) -> None:
    """Ensure S3 bucket exists, create if not.
    
    Args:
        client: S3 client instance
    """
    try:
        await client.head_bucket(Bucket=settings.minio_bucket_name)
    except Exception:
        # Bucket doesn't exist, create it
        await client.create_bucket(Bucket=settings.minio_bucket_name)
