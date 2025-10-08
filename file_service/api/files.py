"""File API endpoints.

This module defines REST API endpoints for file operations including
upload, download, metadata retrieval, and deletion.
"""

from typing import Optional

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)
from fastapi.responses import Response, StreamingResponse

from schemas.file import (
    FileUploadResponse,
    FileResponse,
    FileListResponse,
    FileDownloadResponse,
)
from services.file_service import FileService
from api.deps import get_file_service
from core.config import settings

router = APIRouter(prefix="/files", tags=["files"])


@router.post(
    "/upload",
    response_model=FileUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a file",
    description="Upload a file attachment for a task. Files are stored in S3/MinIO.",
)
async def upload_file(
    file: UploadFile = File(..., description="File to upload"),
    task_id: int = Form(..., description="Associated task ID"),
    uploaded_by: Optional[str] = Form(None, description="Uploader identifier"),
    service: FileService = Depends(get_file_service),
) -> FileUploadResponse:
    """Upload a file for a task.
    
    Args:
        file: File to upload
        task_id: Associated task ID
        uploaded_by: Optional uploader identifier
        service: Injected file service
        
    Returns:
        Upload response with file metadata
        
    Raises:
        HTTPException: If validation fails or upload error occurs
    """
    try:
        file_record, message = await service.upload_file(
            upload_file=file,
            task_id=task_id,
            uploaded_by=uploaded_by,
        )
        
        return FileUploadResponse(
            id=file_record.id,
            task_id=file_record.task_id,
            filename=file_record.filename,
            content_type=file_record.content_type,
            size_bytes=file_record.size_bytes,
            uploaded_at=file_record.uploaded_at,
            message=message,
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload file: {str(e)}",
        )


@router.get(
    "/{file_id}",
    response_model=FileResponse,
    summary="Get file metadata",
    description="Retrieve metadata for a specific file by its ID.",
)
async def get_file_metadata(
    file_id: int,
    service: FileService = Depends(get_file_service),
) -> FileResponse:
    """Get file metadata by ID.
    
    Args:
        file_id: File identifier
        service: Injected file service
        
    Returns:
        File metadata
        
    Raises:
        HTTPException: If file not found (404)
    """
    file_record = await service.get_file(file_id)
    if not file_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File with id {file_id} not found",
        )
    
    return FileResponse.model_validate(file_record)


@router.get(
    "/{file_id}/download-url",
    response_model=FileDownloadResponse,
    summary="Get file download URL",
    description="Generate a presigned URL for downloading the file.",
)
async def get_file_download_url(
    file_id: int,
    service: FileService = Depends(get_file_service),
) -> FileDownloadResponse:
    """Generate presigned download URL for a file.
    
    Args:
        file_id: File identifier
        service: Injected file service
        
    Returns:
        Presigned download URL with metadata
        
    Raises:
        HTTPException: If file not found (404)
    """
    result = await service.get_download_url(file_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File with id {file_id} not found",
        )
    
    download_url, file_record = result
    
    return FileDownloadResponse(
        download_url=download_url,
        filename=file_record.filename,
        content_type=file_record.content_type,
        size_bytes=file_record.size_bytes,
        expires_in_seconds=settings.presigned_url_expiry_seconds,
    )


@router.get(
    "/{file_id}/download",
    summary="Download file",
    description="Download file content directly.",
    response_class=StreamingResponse,
)
async def download_file(
    file_id: int,
    service: FileService = Depends(get_file_service),
) -> StreamingResponse:
    """Download file content.
    
    Args:
        file_id: File identifier
        service: Injected file service
        
    Returns:
        File content as streaming response
        
    Raises:
        HTTPException: If file not found (404)
    """
    result = await service.download_file(file_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File with id {file_id} not found",
        )
    
    file_content, file_record = result
    
    return StreamingResponse(
        iter([file_content]),
        media_type=file_record.content_type,
        headers={
            "Content-Disposition": f'attachment; filename="{file_record.filename}"',
            "Content-Length": str(file_record.size_bytes),
        },
    )


@router.get(
    "/task/{task_id}",
    response_model=FileListResponse,
    summary="Get files by task",
    description="Retrieve all files associated with a specific task.",
)
async def get_files_by_task(
    task_id: int,
    service: FileService = Depends(get_file_service),
) -> FileListResponse:
    """Get all files for a task.
    
    Args:
        task_id: Task identifier
        service: Injected file service
        
    Returns:
        List of files with metadata
    """
    files = await service.get_files_by_task(task_id)
    total = len(files)
    
    return FileListResponse(
        files=[FileResponse.model_validate(f) for f in files],
        total=total,
    )


@router.delete(
    "/{file_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete file",
    description="Delete a file from storage and database.",
)
async def delete_file(
    file_id: int,
    service: FileService = Depends(get_file_service),
) -> None:
    """Delete a file.
    
    Args:
        file_id: File identifier
        service: Injected file service
        
    Raises:
        HTTPException: If file not found (404)
    """
    deleted = await service.delete_file(file_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File with id {file_id} not found",
        )


@router.delete(
    "/task/{task_id}",
    summary="Delete all files for a task",
    description="Delete all files associated with a task. Used when task is deleted.",
)
async def delete_files_by_task(
    task_id: int,
    service: FileService = Depends(get_file_service),
) -> dict:
    """Delete all files for a task.
    
    Args:
        task_id: Task identifier
        service: Injected file service
        
    Returns:
        Dictionary with number of files deleted
    """
    count = await service.delete_files_by_task(task_id)
    
    return {
        "task_id": task_id,
        "files_deleted": count,
        "message": f"Deleted {count} file(s) for task {task_id}",
    }
