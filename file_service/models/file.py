"""File model for storing file metadata.

This module defines the File SQLAlchemy model representing
file metadata stored in the database, while actual file content
is stored in S3/MinIO.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class File(Base):
    """File model representing file metadata.
    
    Stores metadata about uploaded files, while actual file content
    is stored in S3/MinIO object storage. Each file is associated
    with a task from the board service.
    
    Attributes:
        id: Primary key, auto-incrementing integer
        task_id: ID of the associated task from board_service
        filename: Original filename
        file_key: Unique S3 object key for the file
        content_type: MIME type of the file
        size_bytes: File size in bytes
        uploaded_at: Timestamp when file was uploaded
        uploaded_by: Optional user identifier who uploaded the file
    """
    
    __tablename__ = "files"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    task_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_key: Mapped[str] = mapped_column(String(500), unique=True, nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )
    uploaded_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    def __repr__(self) -> str:
        """String representation of File."""
        return f"<File(id={self.id}, filename='{self.filename}', task_id={self.task_id})>"
