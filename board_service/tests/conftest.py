"""Pytest configuration and fixtures for board service tests.

This module provides reusable test fixtures following best practices
for async testing with FastAPI and SQLAlchemy.
"""

import asyncio
from typing import AsyncGenerator, Generator

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from core.database import Base, get_db
from main import app
from models.task import Task, TaskStatus


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
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    async with async_session() as session:
        yield session


@pytest.fixture(scope="function")
async def client(test_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create test HTTP client with database session override."""
    
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield test_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()


@pytest.fixture
async def sample_task(test_session: AsyncSession) -> Task:
    """Create a sample task for testing."""
    task = Task(
        title="Test Task",
        description="Test Description",
        status=TaskStatus.TODO,
    )
    test_session.add(task)
    await test_session.commit()
    await test_session.refresh(task)
    return task


@pytest.fixture
async def multiple_tasks(test_session: AsyncSession) -> list[Task]:
    """Create multiple tasks for testing."""
    tasks = [
        Task(
            title=f"Task {i}",
            description=f"Description {i}",
            status=TaskStatus.TODO if i % 3 == 0 else (
                TaskStatus.IN_PROGRESS if i % 3 == 1 else TaskStatus.DONE
            ),
        )
        for i in range(10)
    ]
    
    for task in tasks:
        test_session.add(task)
    
    await test_session.commit()
    
    for task in tasks:
        await test_session.refresh(task)
    
    return tasks
