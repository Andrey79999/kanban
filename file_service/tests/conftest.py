"""Pytest configuration and fixtures for file service tests."""

import asyncio
from io import BytesIO
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from core.database import Base, get_db
from core.s3 import get_s3_client
from main import app
from models.file import File


# Use in-memory SQLite for testing
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def test_engine():
    """Create test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest.fixture(scope="function")
async def test_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session."""
    async_session = sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )
    
    async with async_session() as session:
        yield session
        await session.commit()


@pytest.fixture(scope="function")
def mock_s3_client():
    """Create mock S3 client for testing."""
    mock_client = AsyncMock()
    
    # Mock common S3 operations
    mock_client.put_object = AsyncMock(return_value={})
    mock_client.get_object = AsyncMock(return_value={
        'Body': AsyncMock(read=AsyncMock(return_value=b"test content"))
    })
    mock_client.delete_object = AsyncMock(return_value={})
    mock_client.head_object = AsyncMock(return_value={'ContentLength': 100})
    mock_client.generate_presigned_url = AsyncMock(
        return_value="https://example.com/presigned-url"
    )
    
    return mock_client


@pytest.fixture(scope="function")
async def client(
    test_session: AsyncSession,
    mock_s3_client
) -> AsyncGenerator[AsyncClient, None]:
    """Create test HTTP client with overrides."""
    
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield test_session
    
    async def override_get_s3_client():
        yield mock_s3_client
    
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_s3_client] = override_get_s3_client
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()


@pytest.fixture
async def sample_file(test_session: AsyncSession) -> File:
    """Create a sample file record for testing."""
    file = File(
        task_id=1,
        filename="test.pdf",
        file_key="tasks/1/test-uuid_test.pdf",
        content_type="application/pdf",
        size_bytes=1024,
        uploaded_by="test_user",
    )
    test_session.add(file)
    await test_session.commit()
    await test_session.refresh(file)
    return file


@pytest.fixture
async def multiple_files(test_session: AsyncSession) -> list[File]:
    """Create multiple file records for testing."""
    files = [
        File(
            task_id=1 if i < 5 else 2,
            filename=f"file{i}.txt",
            file_key=f"tasks/{1 if i < 5 else 2}/uuid{i}_file{i}.txt",
            content_type="text/plain",
            size_bytes=100 * i,
        )
        for i in range(10)
    ]
    
    for file in files:
        test_session.add(file)
    
    await test_session.commit()
    
    for file in files:
        await test_session.refresh(file)
    
    return files


@pytest.fixture
def sample_upload_file():
    """Create a mock UploadFile for testing."""
    from fastapi import UploadFile
    
    file_content = b"test file content"
    file = BytesIO(file_content)
    
    upload_file = UploadFile(
        filename="test_document.pdf",
        file=file,
    )
    upload_file.content_type = "application/pdf"
    
    return upload_file
