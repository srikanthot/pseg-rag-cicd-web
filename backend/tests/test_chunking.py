"""
Unit tests for the chunking service.

Tests deterministic chunking behavior and metadata preservation.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest
from dataclasses import dataclass
from typing import List
import hashlib


@dataclass
class PageContent:
    """Represents extracted content from a single PDF page."""
    page_number: int
    text: str
    has_text: bool


@dataclass
class ExtractedDocument:
    """Represents a fully extracted PDF document."""
    filename: str
    source_url: str
    pages: List[PageContent]
    total_pages: int
    pages_with_text: int


@dataclass
class DocumentChunk:
    """A chunk of text with associated metadata."""
    chunk_id: str
    content: str
    source_file: str
    page_number: int
    source_url: str
    chunk_index: int


class ChunkService:
    """Service for chunking documents into smaller pieces."""
    
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 150,
        min_chunk_size: int = 50
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size
    
    def _generate_chunk_id(
        self,
        filename: str,
        page_number: int,
        chunk_index: int,
        content: str
    ) -> str:
        id_string = f"{filename}:p{page_number}:c{chunk_index}:{content[:50]}"
        return hashlib.md5(id_string.encode()).hexdigest()
    
    def _chunk_text(self, text: str) -> List[str]:
        if not text or len(text) < self.min_chunk_size:
            return [text] if text and text.strip() else []
        
        chunks = []
        start = 0
        text_length = len(text)
        
        while start < text_length:
            end = start + self.chunk_size
            
            if end >= text_length:
                chunk = text[start:]
            else:
                break_point = end
                for sep in ['\n\n', '\n', '. ', ' ']:
                    last_sep = text[start:end].rfind(sep)
                    if last_sep > self.chunk_size * 0.5:
                        break_point = start + last_sep + len(sep)
                        break
                chunk = text[start:break_point]
            
            chunk = chunk.strip()
            if len(chunk) >= self.min_chunk_size:
                chunks.append(chunk)
            
            if end >= text_length:
                break
            
            start = break_point - self.chunk_overlap
            if start < 0:
                start = 0
            if start >= text_length:
                break
        
        return chunks
    
    def chunk_document(self, document: ExtractedDocument) -> List[DocumentChunk]:
        all_chunks: List[DocumentChunk] = []
        
        for page in document.pages:
            if not page.has_text:
                continue
            
            text_chunks = self._chunk_text(page.text)
            
            for idx, chunk_text in enumerate(text_chunks):
                chunk_id = self._generate_chunk_id(
                    document.filename,
                    page.page_number,
                    idx,
                    chunk_text
                )
                
                all_chunks.append(DocumentChunk(
                    chunk_id=chunk_id,
                    content=chunk_text,
                    source_file=document.filename,
                    page_number=page.page_number,
                    source_url=document.source_url,
                    chunk_index=idx
                ))
        
        return all_chunks
    
    def chunk_documents(
        self,
        documents: List[ExtractedDocument]
    ) -> List[DocumentChunk]:
        all_chunks: List[DocumentChunk] = []
        for doc in documents:
            chunks = self.chunk_document(doc)
            all_chunks.extend(chunks)
        return all_chunks


class TestChunkService:
    """Tests for ChunkService."""

    def setup_method(self):
        """Set up test fixtures."""
        self.chunk_service = ChunkService(
            chunk_size=100,
            chunk_overlap=20,
            min_chunk_size=10
        )

    def test_chunk_short_text(self):
        """Test that short text is not split."""
        document = ExtractedDocument(
            filename="test.pdf",
            source_url="https://example.com/test.pdf",
            pages=[
                PageContent(page_number=1, text="Short text.", has_text=True)
            ],
            total_pages=1,
            pages_with_text=1
        )

        chunks = self.chunk_service.chunk_document(document)

        assert len(chunks) == 1
        assert chunks[0].content == "Short text."
        assert chunks[0].source_file == "test.pdf"
        assert chunks[0].page_number == 1

    def test_chunk_long_text(self):
        """Test that long text is split into multiple chunks."""
        long_text = "This is a test sentence. " * 20  # ~500 chars
        document = ExtractedDocument(
            filename="test.pdf",
            source_url="https://example.com/test.pdf",
            pages=[
                PageContent(page_number=1, text=long_text, has_text=True)
            ],
            total_pages=1,
            pages_with_text=1
        )

        chunks = self.chunk_service.chunk_document(document)

        assert len(chunks) > 1
        for chunk in chunks:
            assert len(chunk.content) <= 150  # chunk_size + some buffer
            assert chunk.source_file == "test.pdf"
            assert chunk.page_number == 1

    def test_chunk_preserves_metadata(self):
        """Test that chunking preserves document metadata."""
        document = ExtractedDocument(
            filename="important.pdf",
            source_url="https://storage.blob.core.windows.net/pdfs/important.pdf",
            pages=[
                PageContent(page_number=5, text="Content on page five.", has_text=True)
            ],
            total_pages=10,
            pages_with_text=1
        )

        chunks = self.chunk_service.chunk_document(document)

        assert len(chunks) == 1
        assert chunks[0].source_file == "important.pdf"
        assert chunks[0].page_number == 5
        assert chunks[0].source_url == "https://storage.blob.core.windows.net/pdfs/important.pdf"

    def test_chunk_multiple_pages(self):
        """Test chunking document with multiple pages."""
        document = ExtractedDocument(
            filename="multi.pdf",
            source_url="https://example.com/multi.pdf",
            pages=[
                PageContent(page_number=1, text="Page one content.", has_text=True),
                PageContent(page_number=2, text="Page two content.", has_text=True),
                PageContent(page_number=3, text="Page three content.", has_text=True),
            ],
            total_pages=3,
            pages_with_text=3
        )

        chunks = self.chunk_service.chunk_document(document)

        assert len(chunks) == 3
        assert chunks[0].page_number == 1
        assert chunks[1].page_number == 2
        assert chunks[2].page_number == 3

    def test_chunk_skips_empty_pages(self):
        """Test that pages without text are skipped."""
        document = ExtractedDocument(
            filename="sparse.pdf",
            source_url="https://example.com/sparse.pdf",
            pages=[
                PageContent(page_number=1, text="Has content.", has_text=True),
                PageContent(page_number=2, text="", has_text=False),
                PageContent(page_number=3, text="Also has content.", has_text=True),
            ],
            total_pages=3,
            pages_with_text=2
        )

        chunks = self.chunk_service.chunk_document(document)

        assert len(chunks) == 2
        page_numbers = [c.page_number for c in chunks]
        assert 2 not in page_numbers

    def test_chunk_id_is_deterministic(self):
        """Test that chunk IDs are deterministic for the same input."""
        document = ExtractedDocument(
            filename="test.pdf",
            source_url="https://example.com/test.pdf",
            pages=[
                PageContent(page_number=1, text="Deterministic content.", has_text=True)
            ],
            total_pages=1,
            pages_with_text=1
        )

        chunks1 = self.chunk_service.chunk_document(document)
        chunks2 = self.chunk_service.chunk_document(document)

        assert chunks1[0].chunk_id == chunks2[0].chunk_id

    def test_chunk_id_differs_for_different_content(self):
        """Test that different content produces different chunk IDs."""
        doc1 = ExtractedDocument(
            filename="test.pdf",
            source_url="https://example.com/test.pdf",
            pages=[PageContent(page_number=1, text="Content A.", has_text=True)],
            total_pages=1,
            pages_with_text=1
        )
        doc2 = ExtractedDocument(
            filename="test.pdf",
            source_url="https://example.com/test.pdf",
            pages=[PageContent(page_number=1, text="Content B.", has_text=True)],
            total_pages=1,
            pages_with_text=1
        )

        chunks1 = self.chunk_service.chunk_document(doc1)
        chunks2 = self.chunk_service.chunk_document(doc2)

        assert chunks1[0].chunk_id != chunks2[0].chunk_id

    def test_chunk_overlap(self):
        """Test that chunks have proper overlap."""
        text = "A" * 50 + " " + "B" * 50 + " " + "C" * 50
        document = ExtractedDocument(
            filename="test.pdf",
            source_url="https://example.com/test.pdf",
            pages=[PageContent(page_number=1, text=text, has_text=True)],
            total_pages=1,
            pages_with_text=1
        )

        chunks = self.chunk_service.chunk_document(document)

        assert len(chunks) >= 2

    def test_empty_document(self):
        """Test handling of document with no text."""
        document = ExtractedDocument(
            filename="empty.pdf",
            source_url="https://example.com/empty.pdf",
            pages=[
                PageContent(page_number=1, text="", has_text=False)
            ],
            total_pages=1,
            pages_with_text=0
        )

        chunks = self.chunk_service.chunk_document(document)

        assert len(chunks) == 0

    def test_chunk_documents_multiple(self):
        """Test chunking multiple documents at once."""
        docs = [
            ExtractedDocument(
                filename="doc1.pdf",
                source_url="https://example.com/doc1.pdf",
                pages=[PageContent(page_number=1, text="Doc one.", has_text=True)],
                total_pages=1,
                pages_with_text=1
            ),
            ExtractedDocument(
                filename="doc2.pdf",
                source_url="https://example.com/doc2.pdf",
                pages=[PageContent(page_number=1, text="Doc two.", has_text=True)],
                total_pages=1,
                pages_with_text=1
            ),
        ]

        chunks = self.chunk_service.chunk_documents(docs)

        assert len(chunks) == 2
        filenames = [c.source_file for c in chunks]
        assert "doc1.pdf" in filenames
        assert "doc2.pdf" in filenames
