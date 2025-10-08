"""Application configuration module for file service.

This module handles all configuration settings including database,
S3/MinIO, and file upload constraints.
"""

from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support.
    
    All settings can be overridden via environment variables.
    """

    # Application settings
    app_name: str = Field(default="File Service", description="Application name")
    debug: bool = Field(default=False, description="Debug mode")
    log_level: str = Field(default="INFO", description="Logging level")
    
    # Database settings
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/file_db",
        description="PostgreSQL database connection URL"
    )
    
    # MinIO/S3 settings
    minio_endpoint: str = Field(
        default="localhost:9000",
        description="MinIO endpoint (host:port)"
    )
    minio_access_key: str = Field(
        default="minioadmin",
        description="MinIO access key"
    )
    minio_secret_key: str = Field(
        default="minioadmin",
        description="MinIO secret key"
    )
    minio_bucket_name: str = Field(
        default="kanban-files",
        description="S3 bucket name for file storage"
    )
    minio_secure: bool = Field(
        default=False,
        description="Use HTTPS for MinIO connection"
    )
    
    # File upload settings
    max_file_size_mb: int = Field(
        default=10,
        description="Maximum file size in MB"
    )
    allowed_extensions: List[str] = Field(
        default=[
            ".pdf", ".doc", ".docx", ".txt",
            ".jpg", ".jpeg", ".png", ".gif",
            ".zip", ".rar", ".xlsx", ".xls"
        ],
        description="Allowed file extensions"
    )
    
    # CORS settings
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        description="Allowed CORS origins"
    )
    
    # API settings
    api_v1_prefix: str = Field(default="/api/v1", description="API v1 prefix")
    
    # Presigned URL settings
    presigned_url_expiry_seconds: int = Field(
        default=3600,
        description="Presigned URL expiry time in seconds"
    )
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: str | List[str]) -> List[str]:
        """Parse CORS origins from string or list."""
        if isinstance(v, str):
            import json
            return json.loads(v)
        return v
    
    @field_validator("allowed_extensions", mode="before")
    @classmethod
    def parse_allowed_extensions(cls, v: str | List[str]) -> List[str]:
        """Parse allowed extensions from string or list."""
        if isinstance(v, str):
            if v.startswith("["):
                import json
                return json.loads(v)
            return [ext.strip() for ext in v.split(",")]
        return v
    
    @property
    def max_file_size_bytes(self) -> int:
        """Get maximum file size in bytes."""
        return self.max_file_size_mb * 1024 * 1024


# Global settings instance
settings = Settings()
