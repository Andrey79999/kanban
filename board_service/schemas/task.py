"""Pydantic schemas for task validation and serialization.

These schemas provide request/response validation and automatic
OpenAPI documentation generation.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from models.task import TaskStatus


class TaskBase(BaseModel):
    """Base schema with common task fields."""
    
    title: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Task title",
        examples=["Implement user authentication"]
    )
    description: Optional[str] = Field(
        default=None,
        description="Detailed task description",
        examples=["Add JWT-based authentication with refresh tokens"]
    )


class TaskCreate(TaskBase):
    """Schema for creating a new task.
    
    Status is optional and defaults to 'todo' if not provided.
    """
    
    status: TaskStatus = Field(
        default=TaskStatus.TODO,
        description="Initial task status"
    )
    
    model_config = ConfigDict(use_enum_values=True)


class TaskUpdate(BaseModel):
    """Schema for updating an existing task.
    
    All fields are optional, allowing partial updates.
    """
    
    title: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=200,
        description="Task title"
    )
    description: Optional[str] = Field(
        default=None,
        description="Task description"
    )
    status: Optional[TaskStatus] = Field(
        default=None,
        description="Task status"
    )
    
    model_config = ConfigDict(use_enum_values=True)


class TaskStatusUpdate(BaseModel):
    """Schema for updating only task status.
    
    Used for moving tasks between kanban columns.
    """
    
    status: TaskStatus = Field(
        ...,
        description="New task status",
        examples=[TaskStatus.IN_PROGRESS]
    )
    
    model_config = ConfigDict(use_enum_values=True)


class TaskResponse(TaskBase):
    """Schema for task response with all fields.
    
    Includes auto-generated fields like id and timestamps.
    """
    
    id: int = Field(..., description="Task unique identifier")
    status: TaskStatus = Field(..., description="Current task status")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    files_count: int = Field(default=0, description="Number of attached files")
    
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)


class TaskListResponse(BaseModel):
    """Schema for list of tasks response.
    
    Provides metadata along with the task list.
    """
    
    tasks: List[TaskResponse] = Field(..., description="List of tasks")
    total: int = Field(..., description="Total number of tasks")
    
    model_config = ConfigDict(from_attributes=True)


class WebSocketMessage(BaseModel):
    """Schema for WebSocket messages.
    
    Used for real-time task updates broadcast.
    """
    
    type: str = Field(
        ...,
        description="Message type",
        examples=["task_created", "task_updated", "task_deleted", "task_status_changed"]
    )
    data: dict = Field(..., description="Message payload")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Message timestamp"
    )
