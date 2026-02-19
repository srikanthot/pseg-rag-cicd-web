"""
Health check endpoint for the RAG Chatbot API.

Provides health status and configuration summary for monitoring.
"""

from fastapi import APIRouter

from backend.app import __version__
from backend.app.core.config import settings
from backend.app.models.schemas import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """
    Health check endpoint.
    
    Returns application status and safe configuration summary.
    Used by Azure App Service for health monitoring.
    """
    return HealthResponse(
        status="ok",
        version=__version__,
        config_summary=settings.get_safe_config_summary()
    )


@router.get("/")
async def root():
    """Root endpoint with basic info."""
    return {
        "name": "RAG Chatbot API",
        "version": __version__,
        "docs": "/docs"
    }
