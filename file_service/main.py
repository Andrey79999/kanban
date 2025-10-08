"""Main application entry point for File Service.

This module initializes the FastAPI application with all routers,
middleware, and event handlers for file storage operations.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api import files
from core.config import settings
from core.database import close_db
from core.s3 import ensure_bucket_exists, get_s3_client


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
    print(f"MinIO Endpoint: {settings.minio_endpoint}")
    print(f"Bucket: {settings.minio_bucket_name}")
    
    # Ensure S3 bucket exists
    try:
        async for s3_client in get_s3_client():
            await ensure_bucket_exists(s3_client)
            print(f"S3 bucket '{settings.minio_bucket_name}' is ready")
    except Exception as e:
        print(f"Warning: Could not verify S3 bucket: {e}")
    
    yield
    
    # Shutdown
    print(f"Shutting down {settings.app_name}...")
    await close_db()


# Initialize FastAPI application
app = FastAPI(
    title="File Service API",
    description="""
    ## Kanban File Service
    
    Production-ready microservice for file storage and management.
    
    ### Features
    - ✅ File upload to S3/MinIO storage
    - ✅ File download with presigned URLs
    - ✅ File metadata management
    - ✅ Task-based file organization
    - ✅ File validation (size, extension)
    - ✅ Clean Architecture & SOLID principles
    - ✅ Async/await for all I/O operations
    
    ### Architecture
    - **API Layer**: FastAPI endpoints with automatic OpenAPI docs
    - **Service Layer**: Business logic and validation
    - **Repository Layer**: Data access abstraction
    - **S3 Layer**: Object storage operations
    - **Models**: SQLAlchemy async models
    - **Schemas**: Pydantic validation
    
    ### File Storage
    Files are stored in S3-compatible storage (MinIO) with metadata
    tracked in PostgreSQL. This separation allows efficient storage
    of large files while maintaining fast database queries.
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
    files.router,
    prefix=settings.api_v1_prefix,
)


@app.get("/", tags=["health"])
async def root() -> dict:
    """Root endpoint with service information.
    
    Returns:
        Service information and available endpoints
    """
    return {
        "service": "File Service",
        "version": "1.0.0",
        "status": "running",
        "storage": f"S3 (bucket: {settings.minio_bucket_name})",
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
        "service": "file_service",
        "storage": "s3",
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
        port=8001,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
