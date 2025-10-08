"""File service implementing business logic layer.

This module orchestrates file operations between repository and S3 service,
implementing business rules and validation.
"""

import os
from typing import List, Optional, Tuple

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from types_aiobotocore_s3 import S3Client

from core.config import settings
from models.file import File
from repositories.file_repository import FileRepository
from services.s3_service import S3Service


class FileService:
    """Service for file business logic.
    
    Orchestrates operations between file repository and S3 storage,
    implementing validation and business rules.
    
    Attributes:
        repository: File repository for data access
        s3_service: S3 service for object storage
        session: Database session
    """
    
    def __init__(self, session: AsyncSession, s3_client: S3Client) -> None:
        """Initialize service with database session and S3 client.
        
        Args:
            session: Active database session
            s3_client: Configured S3 client
        """
        self.session = session
        self.repository = FileRepository(session)
        self.s3_service = S3Service(s3_client)
    
    def _validate_file_extension(self, filename: str) -> bool:
        """Validate file extension against allowed list.
        
        Args:
            filename: File name to validate
            
        Returns:
            True if extension is allowed, False otherwise
        """
        ext = os.path.splitext(filename)[1].lower()
        return ext in settings.allowed_extensions
    
    def _validate_file_size(self, size_bytes: int) -> bool:
        """Validate file size against maximum limit.
        
        Args:
            size_bytes: File size in bytes
            
        Returns:
            True if size is within limit, False otherwise
        """
        return size_bytes <= settings.max_file_size_bytes
    
    async def upload_file(
        self,
        upload_file: UploadFile,
        task_id: int,
        uploaded_by: Optional[str] = None,
    ) -> Tuple[File, str]:
        """Upload a file and create metadata record.
        
        Validates file, uploads to S3, and creates database record.
        
        Args:
            upload_file: FastAPI UploadFile object
            task_id: Associated task ID
            uploaded_by: Optional uploader identifier
            
        Returns:
            Tuple of (File instance, success message)
            
        Raises:
            ValueError: If validation fails
        """
        # Validate file extension
        if not self._validate_file_extension(upload_file.filename):
            raise ValueError(
                f"File extension not allowed. Allowed extensions: "
                f"{', '.join(settings.allowed_extensions)}"
            )
        
        # Read file content
        file_content = await upload_file.read()
        file_size = len(file_content)
        
        # Validate file size
        if not self._validate_file_size(file_size):
            raise ValueError(
                f"File size exceeds maximum limit of "
                f"{settings.max_file_size_mb} MB"
            )
        
        # Upload to S3
        file_key = await self.s3_service.upload_file(
            file_content=file_content,
            task_id=task_id,
            filename=upload_file.filename,
            content_type=upload_file.content_type or "application/octet-stream",
        )
        
        # Create database record
        file_record = File(
            task_id=task_id,
            filename=upload_file.filename,
            file_key=file_key,
            content_type=upload_file.content_type or "application/octet-stream",
            size_bytes=file_size,
            uploaded_by=uploaded_by,
        )
        
        file_record = await self.repository.create(file_record)
        
        return file_record, "File uploaded successfully"
    
    async def get_file(self, file_id: int) -> Optional[File]:
        """Retrieve file metadata by ID.
        
        Args:
            file_id: File identifier
            
        Returns:
            File instance if found, None otherwise
        """
        return await self.repository.get_by_id(file_id)
    
    async def get_files_by_task(self, task_id: int) -> List[File]:
        """Retrieve all files for a task.
        
        Args:
            task_id: Task identifier
            
        Returns:
            List of file records
        """
        return await self.repository.get_by_task_id(task_id)
    
    async def get_download_url(self, file_id: int) -> Optional[Tuple[str, File]]:
        """Generate presigned download URL for a file.
        
        Args:
            file_id: File identifier
            
        Returns:
            Tuple of (presigned URL, File instance) if found, None otherwise
        """
        file_record = await self.repository.get_by_id(file_id)
        if not file_record:
            return None
        
        # Generate presigned URL
        download_url = await self.s3_service.generate_presigned_url(
            file_record.file_key
        )
        
        return download_url, file_record
    
    async def download_file(self, file_id: int) -> Optional[Tuple[bytes, File]]:
        """Download file content.
        
        Args:
            file_id: File identifier
            
        Returns:
            Tuple of (file content, File instance) if found, None otherwise
        """
        file_record = await self.repository.get_by_id(file_id)
        if not file_record:
            return None
        
        # Download from S3
        file_content = await self.s3_service.download_file(file_record.file_key)
        
        return file_content, file_record
    
    async def delete_file(self, file_id: int) -> bool:
        """Delete a file from storage and database.
        
        Args:
            file_id: File identifier
            
        Returns:
            True if deleted, False if not found
        """
        file_record = await self.repository.get_by_id(file_id)
        if not file_record:
            return False
        
        # Delete from S3
        await self.s3_service.delete_file(file_record.file_key)
        
        # Delete from database
        await self.repository.delete(file_record)
        
        return True
    
    async def delete_files_by_task(self, task_id: int) -> int:
        """Delete all files associated with a task.
        
        Used when a task is deleted from board service.
        
        Args:
            task_id: Task identifier
            
        Returns:
            Number of files deleted
        """
        files = await self.repository.get_by_task_id(task_id)
        
        # Delete from S3
        for file_record in files:
            await self.s3_service.delete_file(file_record.file_key)
        
        # Delete from database
        count = await self.repository.delete_by_task_id(task_id)
        
        return count
    
    async def count_files(self, task_id: Optional[int] = None) -> int:
        """Count total files, optionally filtered by task.
        
        Args:
            task_id: Optional task ID filter
            
        Returns:
            Total number of files
        """
        return await self.repository.count(task_id=task_id)
