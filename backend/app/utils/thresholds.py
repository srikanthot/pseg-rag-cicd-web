"""
Confidence gating logic for RAG retrieval.

Implements strict grounding to prevent hallucinations by checking
retrieval quality before generating responses.
"""

from dataclasses import dataclass
from typing import List, Optional

from backend.app.models.schemas import RetrievedChunk


@dataclass
class GatingResult:
    """Result of retrieval quality check."""
    
    passed: bool
    reason: str
    top_score: Optional[float] = None
    num_chunks: int = 0


def check_retrieval_quality(
    chunks: List[RetrievedChunk],
    score_threshold: float,
    strict_grounding: bool = True
) -> GatingResult:
    """
    Check if retrieved chunks meet quality threshold for generating a response.
    
    This is the core gating logic that prevents hallucinations by ensuring
    we only generate responses when we have sufficient supporting evidence.
    
    Args:
        chunks: List of retrieved chunks from search
        score_threshold: Minimum score required for top result
        strict_grounding: If True, enforce strict quality checks
        
    Returns:
        GatingResult indicating whether to proceed with generation
    """
    if not chunks:
        return GatingResult(
            passed=False,
            reason="No documents retrieved from search",
            top_score=None,
            num_chunks=0
        )
    
    top_score = max(chunk.score for chunk in chunks)
    
    if strict_grounding and top_score < score_threshold:
        return GatingResult(
            passed=False,
            reason=f"Top retrieval score ({top_score:.3f}) below threshold ({score_threshold})",
            top_score=top_score,
            num_chunks=len(chunks)
        )
    
    return GatingResult(
        passed=True,
        reason="Retrieval quality check passed",
        top_score=top_score,
        num_chunks=len(chunks)
    )


OUT_OF_CONTEXT_MESSAGE = (
    "Your question is outside the provided documents. "
    "I can't answer it from the PDFs I have. "
    "Please ask a question related to the content in the uploaded documents."
)
