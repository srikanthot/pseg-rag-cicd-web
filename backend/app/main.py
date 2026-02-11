"""
FastAPI application entry point for the RAG Chatbot.

Configures the application with all routes and middleware.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app import __version__
from backend.app.api import chat_router, ingest_router, health_router
from backend.app.core.logging import get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup and shutdown events."""
    logger.info(f"RAG Chatbot API v{__version__} starting up")
    yield
    logger.info("RAG Chatbot API shutting down")


app = FastAPI(
    title="RAG Chatbot API",
    description=(
        "Enterprise-grade RAG chatbot using Azure Blob Storage, "
        "Azure AI Search, and Azure OpenAI. Provides grounded responses "
        "with citations from PDF documents."
    ),
    version=__version__,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(chat_router)
app.include_router(ingest_router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
