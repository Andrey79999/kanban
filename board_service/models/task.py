"""Task model for kanban board.

This module defines the Task SQLAlchemy model representing
tasks in the kanban board with three statuses: todo, in_progress, done.
"""

from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional

from sqlalchemy import DateTime, Enum, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class TaskStatus(str, PyEnum):
    """Task status enum representing kanban columns.
    
    Attributes:
        TODO: Task is in 'To Do' column
        IN_PROGRESS: Task is in 'In Progress' column  
        DONE: Task is in 'Done' column
    """
    
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"


class Task(Base):
    """Task model representing a kanban board task.
    
    A task can be in one of three statuses (todo, in_progress, done)
    and can have multiple file attachments linked via file_service.
    
    Attributes:
        id: Primary key, auto-incrementing integer
        title: Task title (required, max 200 chars)
        description: Detailed task description (optional)
        status: Current task status (default: TODO)
        created_at: Timestamp when task was created
        updated_at: Timestamp when task was last updated
    """
    
    __tablename__ = "tasks"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[TaskStatus] = mapped_column(
        Enum(TaskStatus, create_type=False, name='taskstatus', values_callable=lambda x: [e.value for e in x]),
        default=TaskStatus.TODO,
        nullable=False,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )
    
    def __repr__(self) -> str:
        """String representation of Task."""
        return f"<Task(id={self.id}, title='{self.title}', status={self.status})>"
