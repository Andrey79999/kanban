"""Integration tests for task API endpoints.

Tests cover all CRUD operations and edge cases following
Arrange-Act-Assert pattern.
"""

import pytest
from httpx import AsyncClient

from models.task import Task, TaskStatus


class TestCreateTask:
    """Test suite for task creation endpoint."""
    
    @pytest.mark.asyncio
    async def test_create_task_success(self, client: AsyncClient):
        """Test successful task creation."""
        # Arrange
        task_data = {
            "title": "New Task",
            "description": "Task description",
            "status": "TODO",
        }
        
        # Act
        response = await client.post("/api/v1/tasks", json=task_data)
        
        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == task_data["title"]
        assert data["description"] == task_data["description"]
        assert data["status"] == task_data["status"]
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data
    
    @pytest.mark.asyncio
    async def test_create_task_without_description(self, client: AsyncClient):
        """Test task creation without optional description."""
        # Arrange
        task_data = {
            "title": "Task without description",
        }
        
        # Act
        response = await client.post("/api/v1/tasks", json=task_data)
        
        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == task_data["title"]
        assert data["description"] is None
        assert data["status"] == "todo"  # Default status
    
    @pytest.mark.asyncio
    async def test_create_task_with_custom_status(self, client: AsyncClient):
        """Test task creation with custom initial status."""
        # Arrange
        task_data = {
            "title": "In Progress Task",
            "status": "in_progress",
        }
        
        # Act
        response = await client.post("/api/v1/tasks", json=task_data)
        
        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "in_progress"
    
    @pytest.mark.asyncio
    async def test_create_task_validation_error(self, client: AsyncClient):
        """Test task creation with invalid data."""
        # Arrange
        task_data = {
            "title": "",  # Empty title should fail validation
        }
        
        # Act
        response = await client.post("/api/v1/tasks", json=task_data)
        
        # Assert
        assert response.status_code == 422  # Validation error


class TestGetTasks:
    """Test suite for retrieving tasks."""
    
    @pytest.mark.asyncio
    async def test_get_all_tasks_empty(self, client: AsyncClient):
        """Test getting tasks when database is empty."""
        # Act
        response = await client.get("/api/v1/tasks")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["tasks"] == []
        assert data["total"] == 0
    
    @pytest.mark.asyncio
    async def test_get_all_tasks(self, client: AsyncClient, multiple_tasks):
        """Test getting all tasks."""
        # Act
        response = await client.get("/api/v1/tasks")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data["tasks"]) == 10
        assert data["total"] == 10
    
    @pytest.mark.asyncio
    async def test_get_tasks_with_status_filter(self, client: AsyncClient, multiple_tasks):
        """Test filtering tasks by status."""
        # Act
        response = await client.get("/api/v1/tasks?status=todo")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert all(task["status"] == "todo" for task in data["tasks"])
    
    @pytest.mark.asyncio
    async def test_get_tasks_with_pagination(self, client: AsyncClient, multiple_tasks):
        """Test task pagination."""
        # Act
        response = await client.get("/api/v1/tasks?skip=5&limit=3")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data["tasks"]) == 3
        assert data["total"] == 10
    
    @pytest.mark.asyncio
    async def test_get_task_by_id(self, client: AsyncClient, sample_task: Task):
        """Test getting a specific task by ID."""
        # Act
        response = await client.get(f"/api/v1/tasks/{sample_task.id}")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_task.id
        assert data["title"] == sample_task.title
    
    @pytest.mark.asyncio
    async def test_get_task_not_found(self, client: AsyncClient):
        """Test getting non-existent task."""
        # Act
        response = await client.get("/api/v1/tasks/999")
        
        # Assert
        assert response.status_code == 404


class TestUpdateTask:
    """Test suite for task updates."""
    
    @pytest.mark.asyncio
    async def test_update_task_title(self, client: AsyncClient, sample_task: Task):
        """Test updating task title."""
        # Arrange
        update_data = {
            "title": "Updated Title",
        }
        
        # Act
        response = await client.put(
            f"/api/v1/tasks/{sample_task.id}",
            json=update_data
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title"
        assert data["description"] == sample_task.description  # Unchanged
    
    @pytest.mark.asyncio
    async def test_update_task_full(self, client: AsyncClient, sample_task: Task):
        """Test full task update."""
        # Arrange
        update_data = {
            "title": "New Title",
            "description": "New Description",
            "status": "done",
        }
        
        # Act
        response = await client.put(
            f"/api/v1/tasks/{sample_task.id}",
            json=update_data
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "New Title"
        assert data["description"] == "New Description"
        assert data["status"] == "done"
    
    @pytest.mark.asyncio
    async def test_update_task_not_found(self, client: AsyncClient):
        """Test updating non-existent task."""
        # Arrange
        update_data = {"title": "New Title"}
        
        # Act
        response = await client.put("/api/v1/tasks/999", json=update_data)
        
        # Assert
        assert response.status_code == 404


class TestUpdateTaskStatus:
    """Test suite for task status updates (kanban column moves)."""
    
    @pytest.mark.asyncio
    async def test_update_task_status_success(
        self,
        client: AsyncClient,
        sample_task: Task
    ):
        """Test moving task to different status."""
        # Arrange
        status_data = {"status": "in_progress"}
        
        # Act
        response = await client.patch(
            f"/api/v1/tasks/{sample_task.id}/status",
            json=status_data
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "in_progress"
    
    @pytest.mark.asyncio
    async def test_update_task_status_to_done(
        self,
        client: AsyncClient,
        sample_task: Task
    ):
        """Test completing a task."""
        # Arrange
        status_data = {"status": "done"}
        
        # Act
        response = await client.patch(
            f"/api/v1/tasks/{sample_task.id}/status",
            json=status_data
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "done"
    
    @pytest.mark.asyncio
    async def test_update_task_status_not_found(self, client: AsyncClient):
        """Test updating status of non-existent task."""
        # Arrange
        status_data = {"status": "done"}
        
        # Act
        response = await client.patch("/api/v1/tasks/999/status", json=status_data)
        
        # Assert
        assert response.status_code == 404


class TestDeleteTask:
    """Test suite for task deletion."""
    
    @pytest.mark.asyncio
    async def test_delete_task_success(self, client: AsyncClient, sample_task: Task):
        """Test successful task deletion."""
        # Act
        response = await client.delete(f"/api/v1/tasks/{sample_task.id}")
        
        # Assert
        assert response.status_code == 204
        
        # Verify task is deleted
        get_response = await client.get(f"/api/v1/tasks/{sample_task.id}")
        assert get_response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_delete_task_not_found(self, client: AsyncClient):
        """Test deleting non-existent task."""
        # Act
        response = await client.delete("/api/v1/tasks/999")
        
        # Assert
        assert response.status_code == 404
