"""Task API endpoints.

This module defines REST API endpoints for task CRUD operations
and task status management following RESTful best practices.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from models.task import TaskStatus
from schemas.task import (
    TaskCreate,
    TaskListResponse,
    TaskResponse,
    TaskStatusUpdate,
    TaskUpdate,
)
from services.task_service import TaskService
from services.websocket_manager import ws_manager
from api.deps import get_task_service

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post(
    "",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new task",
    description="Create a new task in the kanban board. Default status is 'todo'.",
)
async def create_task(
    task_data: TaskCreate,
    service: TaskService = Depends(get_task_service),
) -> TaskResponse:
    """Create a new task.
    
    Args:
        task_data: Task creation data
        service: Injected task service
        
    Returns:
        Created task with generated ID
        
    Raises:
        HTTPException: If task creation fails
    """
    task = await service.create_task(task_data)
    
    # Broadcast WebSocket event
    task_dict = {
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "status": task.status,
        "created_at": task.created_at.isoformat(),
        "updated_at": task.updated_at.isoformat(),
    }
    await ws_manager.broadcast_task_created(task_dict)
    
    return TaskResponse.model_validate(task)


@router.get(
    "",
    response_model=TaskListResponse,
    summary="Get all tasks",
    description="Retrieve all tasks with optional status filtering and pagination.",
)
async def get_tasks(
    status: Optional[TaskStatus] = Query(
        None,
        description="Filter by task status"
    ),
    skip: int = Query(
        0,
        ge=0,
        description="Number of records to skip"
    ),
    limit: int = Query(
        100,
        ge=1,
        le=1000,
        description="Maximum number of records to return"
    ),
    service: TaskService = Depends(get_task_service),
) -> TaskListResponse:
    """Retrieve all tasks with optional filtering.
    
    Args:
        status: Optional status filter
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return
        service: Injected task service
        
    Returns:
        List of tasks with metadata
    """
    tasks = await service.get_all_tasks(status=status, skip=skip, limit=limit)
    total = await service.count_tasks(status=status)
    
    return TaskListResponse(
        tasks=[TaskResponse.model_validate(task) for task in tasks],
        total=total,
    )


@router.get(
    "/{task_id}",
    response_model=TaskResponse,
    summary="Get task by ID",
    description="Retrieve a specific task by its ID.",
)
async def get_task(
    task_id: int,
    service: TaskService = Depends(get_task_service),
) -> TaskResponse:
    """Retrieve a task by ID.
    
    Args:
        task_id: Task identifier
        service: Injected task service
        
    Returns:
        Task data
        
    Raises:
        HTTPException: If task not found (404)
    """
    task = await service.get_task(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with id {task_id} not found",
        )
    
    return TaskResponse.model_validate(task)


@router.put(
    "/{task_id}",
    response_model=TaskResponse,
    summary="Update task",
    description="Update an existing task. All fields are optional.",
)
async def update_task(
    task_id: int,
    task_data: TaskUpdate,
    service: TaskService = Depends(get_task_service),
) -> TaskResponse:
    """Update an existing task.
    
    Args:
        task_id: Task identifier
        task_data: Updated task data
        service: Injected task service
        
    Returns:
        Updated task data
        
    Raises:
        HTTPException: If task not found (404)
    """
    task = await service.update_task(task_id, task_data)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with id {task_id} not found",
        )
    
    # Broadcast WebSocket event
    task_dict = {
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "status": task.status,
        "created_at": task.created_at.isoformat(),
        "updated_at": task.updated_at.isoformat(),
    }
    await ws_manager.broadcast_task_updated(task_dict)
    
    return TaskResponse.model_validate(task)


@router.patch(
    "/{task_id}/status",
    response_model=TaskResponse,
    summary="Update task status",
    description="Update only the task status. Used for moving tasks between kanban columns.",
)
async def update_task_status(
    task_id: int,
    status_data: TaskStatusUpdate,
    service: TaskService = Depends(get_task_service),
) -> TaskResponse:
    """Update task status (move between kanban columns).
    
    Args:
        task_id: Task identifier
        status_data: New status
        service: Injected task service
        
    Returns:
        Updated task data
        
    Raises:
        HTTPException: If task not found (404)
    """
    # Get old status first
    old_task = await service.get_task(task_id)
    if not old_task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with id {task_id} not found",
        )
    
    old_status = old_task.status
    
    # Update status
    task = await service.update_task_status(task_id, status_data.status)
    
    # Broadcast WebSocket event
    await ws_manager.broadcast_task_status_changed(
        task_id,
        old_status,
        status_data.status,
    )
    
    return TaskResponse.model_validate(task)


@router.delete(
    "/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete task",
    description="Delete a task and all its associated files.",
)
async def delete_task(
    task_id: int,
    service: TaskService = Depends(get_task_service),
) -> None:
    """Delete a task.
    
    Args:
        task_id: Task identifier
        service: Injected task service
        
    Raises:
        HTTPException: If task not found (404)
    """
    deleted = await service.delete_task(task_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with id {task_id} not found",
        )
    
    # Broadcast WebSocket event
    await ws_manager.broadcast_task_deleted(task_id)
