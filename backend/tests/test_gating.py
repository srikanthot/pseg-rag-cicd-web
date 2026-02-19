"""
Unit tests for the retrieval gating logic.

Tests confidence thresholds and out-of-context detection.
"""

import pytest
from dataclasses import dataclass
from typing import List, Optional
from pydantic import BaseModel, Field


class ChunkMetadata(BaseModel):
    """Metadata for a document chunk."""
    source_file: str
    page_number: int
    chunk_id: str
    source_url: str


class RetrievedChunk(BaseModel):
    """A chunk retrieved from the search index."""
    content: str
    score: float
    metadata: ChunkMetadata


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
    """Check if retrieved chunks meet quality threshold."""
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


def create_chunk(score: float, content: str = "Test content") -> RetrievedChunk:
    """Helper to create a test chunk with given score."""
    return RetrievedChunk(
        content=content,
        score=score,
        metadata=ChunkMetadata(
            source_file="test.pdf",
            page_number=1,
            chunk_id="test-chunk-1",
            source_url="https://example.com/test.pdf"
        )
    )


class TestGatingLogic:
    """Tests for retrieval quality gating."""

    def test_empty_chunks_fails_gating(self):
        """Test that empty chunk list fails gating."""
        result = check_retrieval_quality(
            chunks=[],
            score_threshold=0.3,
            strict_grounding=True
        )

        assert result.passed is False
        assert result.num_chunks == 0
        assert result.top_score is None
        assert "No documents retrieved" in result.reason

    def test_low_score_fails_gating_strict_mode(self):
        """Test that low scores fail gating in strict mode."""
        chunks = [create_chunk(0.1), create_chunk(0.2)]

        result = check_retrieval_quality(
            chunks=chunks,
            score_threshold=0.3,
            strict_grounding=True
        )

        assert result.passed is False
        assert result.top_score == 0.2
        assert result.num_chunks == 2
        assert "below threshold" in result.reason

    def test_high_score_passes_gating(self):
        """Test that high scores pass gating."""
        chunks = [create_chunk(0.8), create_chunk(0.5)]

        result = check_retrieval_quality(
            chunks=chunks,
            score_threshold=0.3,
            strict_grounding=True
        )

        assert result.passed is True
        assert result.top_score == 0.8
        assert result.num_chunks == 2

    def test_exact_threshold_passes(self):
        """Test that exact threshold score passes."""
        chunks = [create_chunk(0.3)]

        result = check_retrieval_quality(
            chunks=chunks,
            score_threshold=0.3,
            strict_grounding=True
        )

        assert result.passed is True
        assert result.top_score == 0.3

    def test_low_score_passes_non_strict_mode(self):
        """Test that low scores pass in non-strict mode."""
        chunks = [create_chunk(0.1)]

        result = check_retrieval_quality(
            chunks=chunks,
            score_threshold=0.3,
            strict_grounding=False
        )

        assert result.passed is True
        assert result.top_score == 0.1

    def test_empty_chunks_fails_even_non_strict(self):
        """Test that empty chunks fail even in non-strict mode."""
        result = check_retrieval_quality(
            chunks=[],
            score_threshold=0.3,
            strict_grounding=False
        )

        assert result.passed is False

    def test_uses_max_score(self):
        """Test that gating uses the maximum score from all chunks."""
        chunks = [
            create_chunk(0.1),
            create_chunk(0.5),
            create_chunk(0.2),
        ]

        result = check_retrieval_quality(
            chunks=chunks,
            score_threshold=0.3,
            strict_grounding=True
        )

        assert result.passed is True
        assert result.top_score == 0.5

    def test_different_thresholds(self):
        """Test gating with different threshold values."""
        chunks = [create_chunk(0.5)]

        result_low = check_retrieval_quality(
            chunks=chunks,
            score_threshold=0.1,
            strict_grounding=True
        )
        assert result_low.passed is True

        result_high = check_retrieval_quality(
            chunks=chunks,
            score_threshold=0.9,
            strict_grounding=True
        )
        assert result_high.passed is False

    def test_gating_result_contains_reason(self):
        """Test that gating result always contains a reason."""
        chunks_pass = [create_chunk(0.8)]
        result_pass = check_retrieval_quality(
            chunks=chunks_pass,
            score_threshold=0.3,
            strict_grounding=True
        )
        assert result_pass.reason is not None
        assert len(result_pass.reason) > 0

        chunks_fail = [create_chunk(0.1)]
        result_fail = check_retrieval_quality(
            chunks=chunks_fail,
            score_threshold=0.3,
            strict_grounding=True
        )
        assert result_fail.reason is not None
        assert len(result_fail.reason) > 0


class TestOutOfContextMessage:
    """Tests for the out-of-context message."""

    def test_message_is_professional(self):
        """Test that the out-of-context message is professional."""
        assert "outside the provided documents" in OUT_OF_CONTEXT_MESSAGE
        assert "can't answer" in OUT_OF_CONTEXT_MESSAGE.lower()

    def test_message_mentions_pdfs(self):
        """Test that the message mentions PDFs."""
        assert "PDF" in OUT_OF_CONTEXT_MESSAGE

    def test_message_is_not_empty(self):
        """Test that the message is not empty."""
        assert len(OUT_OF_CONTEXT_MESSAGE) > 50


class TestGatingResultDataclass:
    """Tests for the GatingResult dataclass."""

    def test_gating_result_creation(self):
        """Test creating a GatingResult."""
        result = GatingResult(
            passed=True,
            reason="Test reason",
            top_score=0.8,
            num_chunks=5
        )

        assert result.passed is True
        assert result.reason == "Test reason"
        assert result.top_score == 0.8
        assert result.num_chunks == 5

    def test_gating_result_defaults(self):
        """Test GatingResult default values."""
        result = GatingResult(
            passed=False,
            reason="No results"
        )

        assert result.top_score is None
        assert result.num_chunks == 0
