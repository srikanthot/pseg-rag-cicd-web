"""
Configuration management for the RAG Chatbot application.

Loads environment variables and validates required configuration.
Fails fast with helpful messages if required values are missing.
"""

import os
from functools import lru_cache
from typing import Optional

from pydantic import ConfigDict, Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Azure OpenAI Configuration (Chat Model)
    azure_openai_endpoint: str = Field(
        ...,
        description="Azure OpenAI service endpoint URL for chat model"
    )
    azure_openai_api_key: str = Field(
        ...,
        description="Azure OpenAI API key for chat model"
    )
    azure_openai_api_version: str = Field(
        default="2024-02-15-preview",
        description="Azure OpenAI API version"
    )
    azure_openai_chat_deployment: str = Field(
        ...,
        description="Azure OpenAI chat model deployment name"
    )

    # Azure OpenAI Configuration (Embedding Model - can be in different region)
    azure_openai_embedding_endpoint: Optional[str] = Field(
        default=None,
        description="Azure OpenAI endpoint for embedding model (defaults to main endpoint if not set)"
    )
    azure_openai_embedding_api_key: Optional[str] = Field(
        default=None,
        description="Azure OpenAI API key for embedding model (defaults to main API key if not set)"
    )
    azure_openai_embedding_deployment: str = Field(
        ...,
        description="Azure OpenAI embedding model deployment name"
    )

    # Azure AI Search Configuration
    azure_search_endpoint: str = Field(
        ...,
        description="Azure AI Search service endpoint URL"
    )
    azure_search_api_key: str = Field(
        ...,
        description="Azure AI Search API key"
    )
    azure_search_index_name: str = Field(
        default="rag-documents",
        description="Azure AI Search index name"
    )

    # Azure Blob Storage Configuration
    azure_storage_connection_string: str = Field(
        ...,
        description="Azure Blob Storage connection string"
    )
    azure_storage_container_name: str = Field(
        default="pdfs",
        description="Azure Blob Storage container name for PDFs"
    )
    blob_base_url: Optional[str] = Field(
        default=None,
        description="Base URL for blob storage (for building clickable links)"
    )

    # RAG Tuning Parameters
    top_k: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Number of top results to retrieve"
    )
    score_threshold: float = Field(
        default=0.3,
        ge=0.0,
        le=1.0,
        description="Minimum score threshold for retrieval results"
    )
    strict_grounding: bool = Field(
        default=True,
        description="Enable strict grounding to prevent hallucinations"
    )

    # Backend Configuration
    backend_host: str = Field(
        default="0.0.0.0",
        description="Backend server host"
    )
    backend_port: int = Field(
        default=8000,
        description="Backend server port"
    )

    # Logging
    log_level: str = Field(
        default="INFO",
        description="Logging level"
    )

    @field_validator("azure_openai_endpoint", "azure_search_endpoint")
    @classmethod
    def validate_endpoint_url(cls, v: str) -> str:
        """Validate that endpoint URLs are properly formatted."""
        if not v.startswith("https://"):
            raise ValueError("Endpoint URL must start with https://")
        return v.rstrip("/")

    @field_validator("azure_openai_embedding_endpoint")
    @classmethod
    def validate_embedding_endpoint_url(cls, v: Optional[str]) -> Optional[str]:
        """Validate that embedding endpoint URL is properly formatted if provided."""
        if v is None:
            return v
        if not v.startswith("https://"):
            raise ValueError("Embedding endpoint URL must start with https://")
        return v.rstrip("/")

    def get_embedding_endpoint(self) -> str:
        """Get the effective embedding endpoint (falls back to main endpoint)."""
        return self.azure_openai_embedding_endpoint or self.azure_openai_endpoint

    def get_embedding_api_key(self) -> str:
        """Get the effective embedding API key (falls back to main API key)."""
        return self.azure_openai_embedding_api_key or self.azure_openai_api_key

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level is valid."""
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of: {valid_levels}")
        return v.upper()

    def get_blob_url(self, filename: str) -> str:
        """Build a clickable blob URL for a given filename."""
        if self.blob_base_url:
            base = self.blob_base_url.rstrip("/")
            return f"{base}/{filename}"
        return f"blob://{self.azure_storage_container_name}/{filename}"

    def get_safe_config_summary(self) -> dict:
        """Return a summary of configuration without exposing secrets."""
        return {
            "azure_openai_endpoint": self.azure_openai_endpoint,
            "azure_openai_chat_deployment": self.azure_openai_chat_deployment,
            "azure_openai_embedding_endpoint": self.get_embedding_endpoint(),
            "azure_openai_embedding_deployment": self.azure_openai_embedding_deployment,
            "azure_search_endpoint": self.azure_search_endpoint,
            "azure_search_index_name": self.azure_search_index_name,
            "azure_storage_container_name": self.azure_storage_container_name,
            "top_k": self.top_k,
            "score_threshold": self.score_threshold,
            "strict_grounding": self.strict_grounding,
            "log_level": self.log_level,
        }

    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    
    Raises ValueError with helpful message if required env vars are missing.
    """
    try:
        return Settings()
    except Exception as e:
        missing_vars = []
        required_vars = [
            "AZURE_OPENAI_ENDPOINT",
            "AZURE_OPENAI_API_KEY",
            "AZURE_OPENAI_CHAT_DEPLOYMENT",
            "AZURE_OPENAI_EMBEDDING_DEPLOYMENT",
            "AZURE_SEARCH_ENDPOINT",
            "AZURE_SEARCH_API_KEY",
            "AZURE_STORAGE_CONNECTION_STRING",
        ]
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing_vars)}. "
                f"Please copy .env.example to .env and fill in the values."
            ) from e
        raise


settings = get_settings()
