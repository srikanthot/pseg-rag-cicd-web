"""
Chat endpoint for the RAG Chatbot API.

Handles user questions and returns grounded responses with citations.
"""

from fastapi import APIRouter, HTTPException

from typing import Optional

from backend.app.core.logging import get_logger
from backend.app.models.schemas import ChatRequest, ChatResponse
from backend.app.services.rag_service import RAGService

router = APIRouter(prefix="/api", tags=["chat"])
logger = get_logger(__name__)

_rag_service: Optional[RAGService] = None


def get_rag_service() -> RAGService:
    """Get or create the RAG service singleton."""
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """
    Process a user question and return a grounded response.
    
    The response includes:
    - answer: Generated response or out-of-context message
    - citations: List of source citations with snippets and links
    - out_of_context: Boolean indicating if question is outside documents
    - retrieved_chunks_count: Number of chunks retrieved from search
    
    If no relevant documents are found or confidence is below threshold,
    returns a professional out-of-context message without calling the LLM.
    """
    logger.info(f"Received chat request: {request.question[:50]}...")
    
    try:
        rag_service = get_rag_service()
        response = rag_service.answer_question(
            question=request.question,
            top_k=request.top_k,
            conversation_history=request.conversation_history
        )
        
        if response.out_of_context:
            logger.info("Question determined to be out of context")
        else:
            logger.info(f"Generated response with {len(response.citations)} citations")
        
        return response
        
    except Exception as e:
        logger.error(f"Chat endpoint error: {type(e).__name__}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while processing your question. Please try again."
        )
