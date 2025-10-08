"""File repository implementing data access layer.

This module follows the Repository pattern to abstract database operations
for file metadata storage.
"""

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.file import File


class FileRepository:
    """Repository for File entity database operations.
    
    Implements the Repository pattern to encapsulate all database logic
    for File entities. All methods are async to support non-blocking I/O.
    
    Attributes:
        session: SQLAlchemy async database session
    """
    
    def __init__(self, session: AsyncSession) -> None:
        """Initialize repository with database session.
        
        Args:
            session: Active database session for queries
        """
        self.session = session
    
    async def create(self, file: File) -> File:
        """Create a new file record in the database.
        
        Args:
            file: File instance to create
            
        Returns:
            Created file with generated ID
        """
        self.session.add(file)
        await self.session.flush()
        await self.session.refresh(file)
        return file
    
    async def get_by_id(self, file_id: int) -> Optional[File]:
        """Retrieve a file by its ID.
        
        Args:
            file_id: Unique file identifier
            
        Returns:
            File instance if found, None otherwise
        """
        result = await self.session.execute(
            select(File).where(File.id == file_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_key(self, file_key: str) -> Optional[File]:
        """Retrieve a file by its S3 key.
        
        Args:
            file_key: S3 object key
            
        Returns:
            File instance if found, None otherwise
        """
        result = await self.session.execute(
            select(File).where(File.file_key == file_key)
        )
        return result.scalar_one_or_none()
    
    async def get_by_task_id(self, task_id: int) -> List[File]:
        """Retrieve all files associated with a task.
        
        Args:
            task_id: Task identifier
            
        Returns:
            List of files for the task
        """
        result = await self.session.execute(
            select(File)
            .where(File.task_id == task_id)
            .order_by(File.uploaded_at.desc())
        )
        return list(result.scalars().all())
    
    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> List[File]:
        """Retrieve all files with pagination.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of files
        """
        result = await self.session.execute(
            select(File)
            .offset(skip)
            .limit(limit)
            .order_by(File.uploaded_at.desc())
        )
        return list(result.scalars().all())
    
    async def count(self, task_id: Optional[int] = None) -> int:
        """Count total files, optionally filtered by task.
        
        Args:
            task_id: Optional task ID filter
            
        Returns:
            Total number of files
        """
        from sqlalchemy import func
        
        query = select(func.count(File.id))
        
        if task_id is not None:
            query = query.where(File.task_id == task_id)
        
        result = await self.session.execute(query)
        return result.scalar() or 0
    
    async def delete(self, file: File) -> None:
        """Delete a file record from the database.
        
        Args:
            file: File instance to delete
        """
        await self.session.delete(file)
        await self.session.flush()
    
    async def delete_by_task_id(self, task_id: int) -> int:
        """Delete all files associated with a task.
        
        Args:
            task_id: Task identifier
            
        Returns:
            Number of files deleted
        """
        files = await self.get_by_task_id(task_id)
        count = len(files)
        
        for file in files:
            await self.session.delete(file)
        
        await self.session.flush()
        return count
