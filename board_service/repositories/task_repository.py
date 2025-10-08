"""Task repository implementing data access layer.

This module follows the Repository pattern to abstract database operations
and provide a clean interface for data access, adhering to SOLID principles.
"""

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.task import Task, TaskStatus


class TaskRepository:
    """Repository for Task entity database operations.
    
    Implements the Repository pattern to encapsulate all database logic
    for Task entities. All methods are async to support non-blocking I/O.
    
    Attributes:
        session: SQLAlchemy async database session
    """
    
    def __init__(self, session: AsyncSession) -> None:
        """Initialize repository with database session.
        
        Args:
            session: Active database session for queries
        """
        self.session = session
    
    async def create(self, task: Task) -> Task:
        """Create a new task in the database.
        
        Args:
            task: Task instance to create
            
        Returns:
            Created task with generated ID
            
        Example:
            ```python
            new_task = Task(title="New Task", status=TaskStatus.TODO)
            created = await repo.create(new_task)
            print(created.id)  # Auto-generated ID
            ```
        """
        self.session.add(task)
        await self.session.flush()
        await self.session.refresh(task)
        return task
    
    async def get_by_id(self, task_id: int) -> Optional[Task]:
        """Retrieve a task by its ID.
        
        Args:
            task_id: Unique task identifier
            
        Returns:
            Task instance if found, None otherwise
        """
        result = await self.session.execute(
            select(Task).where(Task.id == task_id)
        )
        return result.scalar_one_or_none()
    
    async def get_all(
        self,
        status: Optional[TaskStatus] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Task]:
        """Retrieve all tasks with optional filtering.
        
        Args:
            status: Optional status filter
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            
        Returns:
            List of tasks matching the criteria
            
        Example:
            ```python
            # Get all tasks in progress
            tasks = await repo.get_all(status=TaskStatus.IN_PROGRESS)
            
            # Get tasks with pagination
            page_2 = await repo.get_all(skip=10, limit=10)
            ```
        """
        query = select(Task)
        
        if status is not None:
            query = query.where(Task.status == status)
        
        query = query.offset(skip).limit(limit).order_by(Task.created_at.desc())
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def count(self, status: Optional[TaskStatus] = None) -> int:
        """Count tasks with optional status filter.
        
        Args:
            status: Optional status filter
            
        Returns:
            Total number of tasks
        """
        from sqlalchemy import func
        
        query = select(func.count(Task.id))
        
        if status is not None:
            query = query.where(Task.status == status)
        
        result = await self.session.execute(query)
        return result.scalar() or 0
    
    async def update(self, task: Task) -> Task:
        """Update an existing task.
        
        Args:
            task: Task instance with updated fields
            
        Returns:
            Updated task instance
            
        Note:
            The task instance should be already attached to the session.
            SQLAlchemy's unit of work will track changes automatically.
        """
        await self.session.flush()
        await self.session.refresh(task)
        return task
    
    async def delete(self, task: Task) -> None:
        """Delete a task from the database.
        
        Args:
            task: Task instance to delete
        """
        await self.session.delete(task)
        await self.session.flush()
    
    async def get_by_status(self, status: TaskStatus) -> List[Task]:
        """Retrieve all tasks with a specific status.
        
        Convenience method for filtering by status without pagination.
        
        Args:
            status: Task status to filter by
            
        Returns:
            List of tasks with the specified status
        """
        result = await self.session.execute(
            select(Task)
            .where(Task.status == status)
            .order_by(Task.created_at.desc())
        )
        return list(result.scalars().all())
