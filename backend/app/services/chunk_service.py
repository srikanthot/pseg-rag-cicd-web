"""
Document chunking service.

Splits extracted text into overlapping chunks suitable for embedding
and retrieval, preserving metadata for citation purposes.
"""

from dataclasses import dataclass
from typing import List
import hashlib

from backend.app.core.logging import get_logger
from backend.app.services.pdf_service import ExtractedDocument, PageContent

logger = get_logger(__name__)


@dataclass
class DocumentChunk:
    """A chunk of text with associated metadata."""
    
    chunk_id: str
    content: str
    source_file: str
    page_number: int
    source_url: str
    chunk_index: int  # Index within the page


class ChunkService:
    """Service for chunking documents into smaller pieces."""
    
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 150,
        min_chunk_size: int = 50
    ):
        """
        Initialize the chunking service.
        
        Args:
            chunk_size: Target size for each chunk in characters (800-1200 recommended)
            chunk_overlap: Number of overlapping characters between chunks
            min_chunk_size: Minimum chunk size to avoid tiny fragments
        """
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
        """Generate a unique, deterministic chunk ID."""
        id_string = f"{filename}:p{page_number}:c{chunk_index}:{content[:50]}"
        return hashlib.md5(id_string.encode()).hexdigest()
    
    def _chunk_text(self, text: str) -> List[str]:
        """
        Split text into overlapping chunks.
        
        Args:
            text: Text to chunk
            
        Returns:
            List of text chunks
        """
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
        """
        Chunk an extracted document into smaller pieces.
        
        Args:
            document: Extracted document with page-wise text
            
        Returns:
            List of DocumentChunk objects
        """
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
        
        logger.info(
            f"Chunked '{document.filename}': "
            f"{len(all_chunks)} chunks from {document.pages_with_text} pages"
        )
        
        return all_chunks
    
    def chunk_documents(
        self,
        documents: List[ExtractedDocument]
    ) -> List[DocumentChunk]:
        """
        Chunk multiple documents.
        
        Args:
            documents: List of extracted documents
            
        Returns:
            Combined list of all chunks
        """
        all_chunks: List[DocumentChunk] = []
        
        for doc in documents:
            chunks = self.chunk_document(doc)
            all_chunks.extend(chunks)
        
        logger.info(f"Total chunks created: {len(all_chunks)} from {len(documents)} documents")
        return all_chunks
