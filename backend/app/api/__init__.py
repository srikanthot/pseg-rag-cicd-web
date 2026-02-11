"""API routes for the RAG Chatbot."""

from .routes_chat import router as chat_router
from .routes_ingest import router as ingest_router
from .routes_health import router as health_router

__all__ = ["chat_router", "ingest_router", "health_router"]
