"""Dependency injection for API endpoints.

This module provides FastAPI dependencies for services and repositories,
implementing dependency injection pattern for clean architecture.
"""

from typing import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from services.task_service import TaskService


async def get_task_service(
    db_session: AsyncSession = Depends(get_db),
) -> TaskService:
    """Dependency for task service injection.
    
    Args:
        db_session: Database session from get_db dependency
    
    Returns:
        TaskService instance with active database session
        
    Example:
        ```python
        @app.post("/tasks")
        async def create_task(
            task_data: TaskCreate,
            service: TaskService = Depends(get_task_service)
        ):
            return await service.create_task(task_data)
        ```
    """
    return TaskService(db_session)
