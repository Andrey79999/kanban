"""Task service implementing business logic layer.

This module contains the business logic for task operations,
separating concerns between API endpoints and data access.
"""

from typing import List, Optional

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from models.task import Task, TaskStatus
from repositories.task_repository import TaskRepository
from schemas.task import TaskCreate, TaskUpdate


class TaskService:
    """Service for task business logic.
    
    Implements business rules and orchestrates operations between
    different layers (repository, external services, etc.).
    
    Attributes:
        repository: Task repository for data access
        session: Database session
    """
    
    def __init__(self, session: AsyncSession) -> None:
        """Initialize service with database session.
        
        Args:
            session: Active database session
        """
        self.session = session
        self.repository = TaskRepository(session)
    
    async def create_task(self, task_data: TaskCreate) -> Task:
        """Create a new task.
        
        Args:
            task_data: Task creation data
            
        Returns:
            Created task instance
            
        Raises:
            ValueError: If task data is invalid
        """
        task = Task(
            title=task_data.title,
            description=task_data.description,
            status=task_data.status,
        )
        return await self.repository.create(task)
    
    async def get_task(self, task_id: int) -> Optional[Task]:
        """Retrieve a task by ID.
        
        Args:
            task_id: Task identifier
            
        Returns:
            Task instance if found, None otherwise
        """
        return await self.repository.get_by_id(task_id)
    
    async def get_all_tasks(
        self,
        status: Optional[TaskStatus] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Task]:
        """Retrieve all tasks with optional filtering.
        
        Args:
            status: Optional status filter
            skip: Number of records to skip
            limit: Maximum number of records
            
        Returns:
            List of tasks
        """
        return await self.repository.get_all(status=status, skip=skip, limit=limit)
    
    async def count_tasks(self, status: Optional[TaskStatus] = None) -> int:
        """Count total tasks.
        
        Args:
            status: Optional status filter
            
        Returns:
            Total number of tasks
        """
        return await self.repository.count(status=status)
    
    async def update_task(self, task_id: int, task_data: TaskUpdate) -> Optional[Task]:
        """Update an existing task.
        
        Args:
            task_id: Task identifier
            task_data: Updated task data
            
        Returns:
            Updated task if found, None otherwise
        """
        task = await self.repository.get_by_id(task_id)
        if not task:
            return None
        
        # Update only provided fields
        if task_data.title is not None:
            task.title = task_data.title
        if task_data.description is not None:
            task.description = task_data.description
        if task_data.status is not None:
            task.status = task_data.status
        
        return await self.repository.update(task)
    
    async def update_task_status(
        self,
        task_id: int,
        new_status: TaskStatus
    ) -> Optional[Task]:
        """Update task status (move between kanban columns).
        
        Args:
            task_id: Task identifier
            new_status: New task status
            
        Returns:
            Updated task if found, None otherwise
        """
        task = await self.repository.get_by_id(task_id)
        if not task:
            return None
        
        task.status = new_status
        return await self.repository.update(task)
    
    async def delete_task(self, task_id: int) -> bool:
        """Delete a task and its associated files.
        
        This method also calls the file service to delete all
        associated file attachments.
        
        Args:
            task_id: Task identifier
            
        Returns:
            True if task was deleted, False if not found
        """
        task = await self.repository.get_by_id(task_id)
        if not task:
            return False
        
        # Delete associated files from file service
        await self._delete_task_files(task_id)
        
        # Delete the task
        await self.repository.delete(task)
        return True
    
    async def _delete_task_files(self, task_id: int) -> None:
        """Delete all files associated with a task.
        
        Calls the file service API to delete files.
        Errors are logged but don't prevent task deletion.
        
        Args:
            task_id: Task identifier
        """
        try:
            async with httpx.AsyncClient() as client:
                url = f"{settings.file_service_url}/api/v1/files/task/{task_id}"
                response = await client.delete(url, timeout=10.0)
                response.raise_for_status()
        except Exception as e:
            # Log error but don't fail task deletion
            # In production, use proper logging
            print(f"Warning: Failed to delete files for task {task_id}: {e}")
    
    async def get_tasks_by_status(self, status: TaskStatus) -> List[Task]:
        """Retrieve all tasks with specific status.
        
        Convenience method for filtering by status.
        
        Args:
            status: Task status to filter by
            
        Returns:
            List of tasks with the specified status
        """
        return await self.repository.get_by_status(status)
