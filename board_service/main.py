"""Main application entry point for Board Service.

This module initializes the FastAPI application with all routers,
middleware, and event handlers following production-ready practices.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api import tasks, websocket
from core.config import settings
from core.database import close_db


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager.
    
    Handles startup and shutdown events for proper resource management.
    
    Args:
        app: FastAPI application instance
    """
    # Startup
    print(f"Starting {settings.app_name}...")
    print(f"Database URL: {settings.database_url}")
    print(f"File Service URL: {settings.file_service_url}")
    
    yield
    
    # Shutdown
    print(f"Shutting down {settings.app_name}...")
    await close_db()


# Initialize FastAPI application
app = FastAPI(
    title="Board Service API",
    description="""
    ## Kanban Board Service
    
    Production-ready microservice for managing kanban board tasks.
    
    ### Features
    - ✅ CRUD operations for tasks
    - ✅ Task status management (todo → in_progress → done)
    - ✅ Real-time updates via WebSocket
    - ✅ Integration with file service
    - ✅ Clean Architecture & SOLID principles
    - ✅ Async/await for all I/O operations
    
    ### Architecture
    - **API Layer**: FastAPI endpoints with automatic OpenAPI docs
    - **Service Layer**: Business logic and orchestration
    - **Repository Layer**: Data access abstraction
    - **Models**: SQLAlchemy async models
    - **Schemas**: Pydantic validation
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(
    tasks.router,
    prefix=settings.api_v1_prefix,
)
app.include_router(websocket.router)


@app.get("/", tags=["health"])
async def root() -> dict:
    """Root endpoint with service information.
    
    Returns:
        Service information and available endpoints
    """
    return {
        "service": "Board Service",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health", tags=["health"])
async def health_check() -> dict:
    """Health check endpoint.
    
    Returns:
        Service health status
    """
    return {
        "status": "healthy",
        "service": "board_service",
    }


@app.exception_handler(Exception)
async def global_exception_handler(request, exc: Exception) -> JSONResponse:
    """Global exception handler for unhandled exceptions.
    
    Args:
        request: Request that caused the exception
        exc: Exception that was raised
        
    Returns:
        JSON error response
    """
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "error": str(exc) if settings.debug else "An error occurred",
        },
    )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
