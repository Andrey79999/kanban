"""Pydantic schemas for file validation and serialization."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class FileBase(BaseModel):
    """Base schema with common file fields."""
    
    filename: str = Field(
        ...,
        description="Original filename",
        examples=["document.pdf"]
    )
    content_type: str = Field(
        ...,
        description="MIME type of the file",
        examples=["application/pdf"]
    )
    size_bytes: int = Field(
        ...,
        ge=0,
        description="File size in bytes"
    )


class FileUploadResponse(BaseModel):
    """Schema for file upload response."""
    
    id: int = Field(..., description="File unique identifier")
    task_id: int = Field(..., description="Associated task ID")
    filename: str = Field(..., description="Original filename")
    content_type: str = Field(..., description="File MIME type")
    size_bytes: int = Field(..., description="File size in bytes")
    uploaded_at: datetime = Field(..., description="Upload timestamp")
    message: str = Field(
        default="File uploaded successfully",
        description="Success message"
    )
    
    model_config = ConfigDict(from_attributes=True)


class FileResponse(BaseModel):
    """Schema for file metadata response."""
    
    id: int = Field(..., description="File unique identifier")
    task_id: int = Field(..., description="Associated task ID")
    filename: str = Field(..., description="Original filename")
    file_key: str = Field(..., description="S3 object key")
    content_type: str = Field(..., description="File MIME type")
    size_bytes: int = Field(..., description="File size in bytes")
    uploaded_at: datetime = Field(..., description="Upload timestamp")
    uploaded_by: Optional[str] = Field(None, description="Uploader identifier")
    
    model_config = ConfigDict(from_attributes=True)


class FileListResponse(BaseModel):
    """Schema for list of files response."""
    
    files: List[FileResponse] = Field(..., description="List of files")
    total: int = Field(..., description="Total number of files")
    
    model_config = ConfigDict(from_attributes=True)


class FileDownloadResponse(BaseModel):
    """Schema for file download URL response."""
    
    download_url: str = Field(..., description="Presigned download URL")
    filename: str = Field(..., description="Original filename")
    content_type: str = Field(..., description="File MIME type")
    size_bytes: int = Field(..., description="File size in bytes")
    expires_in_seconds: int = Field(
        ...,
        description="URL expiry time in seconds"
    )
    
    model_config = ConfigDict(from_attributes=True)
