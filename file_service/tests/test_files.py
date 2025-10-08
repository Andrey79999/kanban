"""Integration tests for file API endpoints.

Tests cover file upload, download, metadata retrieval, and deletion
with proper mocking of S3 operations.
"""

from io import BytesIO
from unittest.mock import AsyncMock

import pytest
from httpx import AsyncClient

from models.file import File


class TestFileUpload:
    """Test suite for file upload endpoint."""
    
    @pytest.mark.asyncio
    async def test_upload_file_success(self, client: AsyncClient, mock_s3_client):
        """Test successful file upload."""
        # Arrange
        file_content = b"test file content"
        files = {
            "file": ("test.pdf", BytesIO(file_content), "application/pdf")
        }
        data = {"task_id": 1}
        
        # Act
        response = await client.post(
            "/api/v1/files/upload",
            files=files,
            data=data
        )
        
        # Assert
        assert response.status_code == 201
        result = response.json()
        assert result["filename"] == "test.pdf"
        assert result["task_id"] == 1
        assert result["content_type"] == "application/pdf"
        assert "id" in result
        assert "uploaded_at" in result
        
        # Verify S3 upload was called
        mock_s3_client.put_object.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_upload_file_with_uploader(
        self,
        client: AsyncClient,
        mock_s3_client
    ):
        """Test file upload with uploader identifier."""
        # Arrange
        file_content = b"test content"
        files = {
            "file": ("document.pdf", BytesIO(file_content), "application/pdf")
        }
        data = {
            "task_id": 1,
            "uploaded_by": "user123"
        }
        
        # Act
        response = await client.post(
            "/api/v1/files/upload",
            files=files,
            data=data
        )
        
        # Assert
        assert response.status_code == 201
        result = response.json()
        assert result["task_id"] == 1
    
    @pytest.mark.asyncio
    async def test_upload_file_size_validation(
        self,
        client: AsyncClient,
        mock_s3_client
    ):
        """Test file size validation."""
        # Arrange - Create file larger than limit (default 10MB)
        large_content = b"x" * (11 * 1024 * 1024)  # 11 MB
        files = {
            "file": ("large.pdf", BytesIO(large_content), "application/pdf")
        }
        data = {"task_id": 1}
        
        # Act
        response = await client.post(
            "/api/v1/files/upload",
            files=files,
            data=data
        )
        
        # Assert
        assert response.status_code == 400
        assert "size exceeds" in response.json()["detail"].lower()


class TestGetFileMetadata:
    """Test suite for file metadata retrieval."""
    
    @pytest.mark.asyncio
    async def test_get_file_metadata_success(
        self,
        client: AsyncClient,
        sample_file: File
    ):
        """Test retrieving file metadata."""
        # Act
        response = await client.get(f"/api/v1/files/{sample_file.id}")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_file.id
        assert data["filename"] == sample_file.filename
        assert data["task_id"] == sample_file.task_id
        assert data["content_type"] == sample_file.content_type
        assert data["size_bytes"] == sample_file.size_bytes
    
    @pytest.mark.asyncio
    async def test_get_file_metadata_not_found(self, client: AsyncClient):
        """Test retrieving non-existent file metadata."""
        # Act
        response = await client.get("/api/v1/files/999")
        
        # Assert
        assert response.status_code == 404


class TestGetFilesByTask:
    """Test suite for retrieving files by task."""
    
    @pytest.mark.asyncio
    async def test_get_files_by_task_success(
        self,
        client: AsyncClient,
        multiple_files: list[File]
    ):
        """Test getting all files for a task."""
        # Act
        response = await client.get("/api/v1/files/task/1")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data["files"]) == 5  # 5 files for task_id 1
        assert data["total"] == 5
        assert all(f["task_id"] == 1 for f in data["files"])
    
    @pytest.mark.asyncio
    async def test_get_files_by_task_empty(self, client: AsyncClient):
        """Test getting files for task with no files."""
        # Act
        response = await client.get("/api/v1/files/task/999")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["files"] == []
        assert data["total"] == 0


class TestFileDownload:
    """Test suite for file download endpoints."""
    
    @pytest.mark.asyncio
    async def test_get_download_url_success(
        self,
        client: AsyncClient,
        sample_file: File,
        mock_s3_client
    ):
        """Test generating presigned download URL."""
        # Act
        response = await client.get(
            f"/api/v1/files/{sample_file.id}/download-url"
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "download_url" in data
        assert data["filename"] == sample_file.filename
        assert data["content_type"] == sample_file.content_type
        assert "expires_in_seconds" in data
        
        # Verify presigned URL was generated
        mock_s3_client.generate_presigned_url.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_download_url_not_found(self, client: AsyncClient):
        """Test generating download URL for non-existent file."""
        # Act
        response = await client.get("/api/v1/files/999/download-url")
        
        # Assert
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_download_file_success(
        self,
        client: AsyncClient,
        sample_file: File,
        mock_s3_client
    ):
        """Test direct file download."""
        # Arrange
        class MockBody:
            async def __aenter__(self):
                return self
            async def __aexit__(self, *args):
                pass
            async def read(self):
                return b"test content"
        
        mock_s3_client.get_object.return_value = {'Body': MockBody()}
        
        # Act
        response = await client.get(f"/api/v1/files/{sample_file.id}/download")
        
        # Assert
        assert response.status_code == 200
        assert response.content == b"test content"
        assert "attachment" in response.headers["content-disposition"]
        
        # Verify S3 download was called
        mock_s3_client.get_object.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_download_file_not_found(self, client: AsyncClient):
        """Test downloading non-existent file."""
        # Act
        response = await client.get("/api/v1/files/999/download")
        
        # Assert
        assert response.status_code == 404


class TestDeleteFile:
    """Test suite for file deletion."""
    
    @pytest.mark.asyncio
    async def test_delete_file_success(
        self,
        client: AsyncClient,
        sample_file: File,
        mock_s3_client
    ):
        """Test successful file deletion."""
        # Act
        response = await client.delete(f"/api/v1/files/{sample_file.id}")
        
        # Assert
        assert response.status_code == 204
        
        # Verify file is deleted from database
        get_response = await client.get(f"/api/v1/files/{sample_file.id}")
        assert get_response.status_code == 404
        
        # Verify S3 deletion was called
        mock_s3_client.delete_object.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_delete_file_not_found(self, client: AsyncClient):
        """Test deleting non-existent file."""
        # Act
        response = await client.delete("/api/v1/files/999")
        
        # Assert
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_delete_files_by_task(
        self,
        client: AsyncClient,
        multiple_files: list[File],
        mock_s3_client
    ):
        """Test deleting all files for a task."""
        # Act
        response = await client.delete("/api/v1/files/task/1")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == 1
        assert data["files_deleted"] == 5
        
        # Verify files are deleted from database
        get_response = await client.get("/api/v1/files/task/1")
        assert get_response.json()["total"] == 0
        
        # Verify S3 deletions were called
        assert mock_s3_client.delete_object.call_count == 5
