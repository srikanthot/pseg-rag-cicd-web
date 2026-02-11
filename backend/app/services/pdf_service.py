"""
PDF text extraction service.

Extracts text content from PDF documents on a page-by-page basis
using PyMuPDF (fitz) for reliable text extraction.
"""

from dataclasses import dataclass
from typing import List, Optional
from io import BytesIO

import fitz  # PyMuPDF

from backend.app.core.logging import get_logger
from backend.app.utils.text import clean_text

logger = get_logger(__name__)


@dataclass
class PageContent:
    """Represents extracted content from a single PDF page."""
    
    page_number: int  # 1-indexed
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


class PDFService:
    """Service for extracting text from PDF documents."""
    
    def extract_text(
        self,
        pdf_content: bytes,
        filename: str,
        source_url: str
    ) -> ExtractedDocument:
        """
        Extract text from a PDF document page by page.
        
        Args:
            pdf_content: Raw PDF bytes
            filename: Original filename for logging
            source_url: URL to the source document
            
        Returns:
            ExtractedDocument with page-wise text content
        """
        pages: List[PageContent] = []
        pages_with_text = 0
        
        try:
            pdf_stream = BytesIO(pdf_content)
            doc = fitz.open(stream=pdf_stream, filetype="pdf")
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                raw_text = page.get_text()
                cleaned_text = clean_text(raw_text)
                
                has_text = bool(cleaned_text and len(cleaned_text.strip()) > 10)
                
                if has_text:
                    pages_with_text += 1
                
                pages.append(PageContent(
                    page_number=page_num + 1,  # 1-indexed
                    text=cleaned_text,
                    has_text=has_text
                ))
            
            doc.close()
            
            if pages_with_text == 0:
                logger.warning(
                    f"PDF '{filename}' has no extractable text (possibly scanned). "
                    f"Total pages: {len(pages)}"
                )
            else:
                logger.info(
                    f"Extracted text from '{filename}': "
                    f"{pages_with_text}/{len(pages)} pages with text"
                )
            
            return ExtractedDocument(
                filename=filename,
                source_url=source_url,
                pages=pages,
                total_pages=len(pages),
                pages_with_text=pages_with_text
            )
            
        except Exception as e:
            logger.error(f"Error extracting text from '{filename}': {type(e).__name__}")
            raise
    
    def has_extractable_text(self, extracted_doc: ExtractedDocument) -> bool:
        """
        Check if a document has any extractable text.
        
        Args:
            extracted_doc: Previously extracted document
            
        Returns:
            True if document has at least one page with text
        """
        return extracted_doc.pages_with_text > 0
