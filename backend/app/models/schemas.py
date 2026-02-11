"""
Pydantic request/response models for the RAG Chatbot API.

Defines all data structures used in API communication.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class ChunkMetadata(BaseModel):
    """Metadata for a document chunk."""

    source_file: str = Field(..., description="Original PDF filename")
    page_number: Optional[int] = Field(default=None, description="Page number in the PDF (1-indexed)")
    chunk_id: str = Field(..., description="Unique identifier for the chunk")
    source_url: str = Field(..., description="Clickable URL to the source document")


class RetrievedChunk(BaseModel):
    """A chunk retrieved from the search index."""
    
    content: str = Field(..., description="Text content of the chunk")
    score: float = Field(..., description="Relevance score from search")
    metadata: ChunkMetadata = Field(..., description="Chunk metadata")


class Citation(BaseModel):
    """Citation for a source used in generating the answer."""

    source_file: str = Field(..., description="PDF filename")
    page_number: Optional[int] = Field(default=None, description="Page number (1-indexed)")
    source_url: str = Field(..., description="Clickable link to the document")
    snippet: str = Field(..., description="Relevant text snippet from the source")


class ConversationMessage(BaseModel):
    """A single message in the conversation history."""

    role: str = Field(..., description="Message role: 'user' or 'assistant'")
    content: str = Field(..., description="Message content")


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""

    question: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="User's question"
    )
    top_k: Optional[int] = Field(
        default=None,
        ge=1,
        le=20,
        description="Number of documents to retrieve (overrides default)"
    )
    conversation_history: Optional[List[ConversationMessage]] = Field(
        default=None,
        description="Previous conversation messages for context continuity"
    )


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""
    
    answer: str = Field(..., description="Generated answer or out-of-context message")
    citations: List[Citation] = Field(
        default_factory=list,
        description="List of citations supporting the answer"
    )
    out_of_context: bool = Field(
        default=False,
        description="True if question is outside provided documents"
    )
    retrieved_chunks_count: int = Field(
        default=0,
        description="Number of chunks retrieved from search"
    )


class IngestRequest(BaseModel):
    """Request model for ingest endpoint."""
    
    force_reindex: bool = Field(
        default=False,
        description="Force re-indexing of all documents"
    )


class IngestResponse(BaseModel):
    """Response model for ingest endpoint."""
    
    success: bool = Field(..., description="Whether ingestion was successful")
    num_pdfs_processed: int = Field(default=0, description="Number of PDFs processed")
    num_chunks_indexed: int = Field(default=0, description="Number of chunks indexed")
    num_failures: int = Field(default=0, description="Number of failures")
    message: str = Field(default="", description="Status message")
    details: Optional[List[str]] = Field(
        default=None,
        description="Detailed processing information"
    )


class HealthResponse(BaseModel):
    """Response model for health endpoint."""
    
    status: str = Field(..., description="Health status")
    version: str = Field(..., description="Application version")
    config_summary: dict = Field(
        default_factory=dict,
        description="Safe configuration summary (no secrets)"
    )
