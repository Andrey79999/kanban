"""S3 service for object storage operations.

This module provides high-level S3/MinIO operations for file storage,
including upload, download, deletion, and presigned URL generation.
"""

import uuid
from typing import BinaryIO, Optional

from botocore.exceptions import ClientError
from types_aiobotocore_s3 import S3Client

from core.config import settings


class S3Service:
    """Service for S3/MinIO operations.
    
    Provides abstraction layer for object storage operations.
    All methods are async for non-blocking I/O.
    
    Attributes:
        client: Async S3 client
        bucket_name: S3 bucket name for file storage
    """
    
    def __init__(self, client: S3Client) -> None:
        """Initialize S3 service with client.
        
        Args:
            client: Configured async S3 client
        """
        self.client = client
        self.bucket_name = settings.minio_bucket_name
    
    def _generate_file_key(
        self,
        task_id: int,
        filename: str
    ) -> str:
        """Generate unique S3 object key for a file.
        
        Uses task_id and UUID to ensure uniqueness and organize files.
        
        Args:
            task_id: Associated task ID
            filename: Original filename
            
        Returns:
            Unique S3 object key
            
        Example:
            "tasks/123/4a3b8e2f-abc1-4567-89ab-cdef01234567_document.pdf"
        """
        unique_id = str(uuid.uuid4())
        # Sanitize filename
        safe_filename = filename.replace(" ", "_")
        return f"tasks/{task_id}/{unique_id}_{safe_filename}"
    
    async def upload_file(
        self,
        file_content: bytes,
        task_id: int,
        filename: str,
        content_type: str,
    ) -> str:
        """Upload a file to S3 storage.
        
        Args:
            file_content: File binary content
            task_id: Associated task ID
            filename: Original filename
            content_type: MIME type
            
        Returns:
            S3 object key of uploaded file
            
        Raises:
            ClientError: If upload fails
        """
        file_key = self._generate_file_key(task_id, filename)
        
        await self.client.put_object(
            Bucket=self.bucket_name,
            Key=file_key,
            Body=file_content,
            ContentType=content_type,
            Metadata={
                'task_id': str(task_id),
                'original_filename': filename,
            }
        )
        
        return file_key
    
    async def download_file(self, file_key: str) -> bytes:
        """Download a file from S3 storage.
        
        Args:
            file_key: S3 object key
            
        Returns:
            File binary content
            
        Raises:
            ClientError: If file not found or download fails
        """
        response = await self.client.get_object(
            Bucket=self.bucket_name,
            Key=file_key,
        )
        
        async with response['Body'] as stream:
            return await stream.read()
    
    async def delete_file(self, file_key: str) -> bool:
        """Delete a file from S3 storage.
        
        Args:
            file_key: S3 object key
            
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            await self.client.delete_object(
                Bucket=self.bucket_name,
                Key=file_key,
            )
            return True
        except ClientError as e:
            print(f"Error deleting file {file_key}: {e}")
            return False
    
    async def file_exists(self, file_key: str) -> bool:
        """Check if a file exists in S3 storage.
        
        Args:
            file_key: S3 object key
            
        Returns:
            True if file exists, False otherwise
        """
        try:
            await self.client.head_object(
                Bucket=self.bucket_name,
                Key=file_key,
            )
            return True
        except ClientError:
            return False
    
    async def generate_presigned_url(
        self,
        file_key: str,
        expiry_seconds: Optional[int] = None,
    ) -> str:
        """Generate a presigned URL for file download.
        
        Creates a temporary URL that allows direct download without authentication.
        
        Args:
            file_key: S3 object key
            expiry_seconds: URL expiry time (default from settings)
            
        Returns:
            Presigned download URL
        """
        if expiry_seconds is None:
            expiry_seconds = settings.presigned_url_expiry_seconds
        
        url = await self.client.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': self.bucket_name,
                'Key': file_key,
            },
            ExpiresIn=expiry_seconds,
        )
        
        return url
    
    async def get_file_size(self, file_key: str) -> Optional[int]:
        """Get file size in bytes.
        
        Args:
            file_key: S3 object key
            
        Returns:
            File size in bytes, None if file not found
        """
        try:
            response = await self.client.head_object(
                Bucket=self.bucket_name,
                Key=file_key,
            )
            return response.get('ContentLength')
        except ClientError:
            return None
