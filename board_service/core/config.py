"""Application configuration module.

This module handles all configuration settings for the board service,
including database connections, external service URLs, and application settings.
"""

from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support.
    
    All settings can be overridden via environment variables.
    Follows the 12-factor app methodology for configuration management.
    """

    # Application settings
    app_name: str = Field(default="Board Service", description="Application name")
    debug: bool = Field(default=False, description="Debug mode")
    log_level: str = Field(default="INFO", description="Logging level")
    
    # Database settings
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/board_db",
        description="PostgreSQL database connection URL"
    )
    
    # External services
    file_service_url: str = Field(
        default="http://localhost:8001",
        description="File service base URL"
    )
    
    # CORS settings
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        description="Allowed CORS origins"
    )
    
    # WebSocket settings
    ws_heartbeat_interval: int = Field(
        default=30,
        description="WebSocket heartbeat interval in seconds"
    )
    
    # API settings
    api_v1_prefix: str = Field(default="/api/v1", description="API v1 prefix")
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: str | List[str]) -> List[str]:
        """Parse CORS origins from string or list.
        
        Args:
            v: CORS origins as string (JSON array) or list
            
        Returns:
            List of CORS origin URLs
        """
        if isinstance(v, str):
            import json
            return json.loads(v)
        return v


# Global settings instance
settings = Settings()
