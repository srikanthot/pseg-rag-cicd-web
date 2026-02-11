"""
Ingestion endpoint for the RAG Chatbot API.

Handles PDF ingestion from Azure Blob Storage into Azure AI Search.
"""

from fastapi import APIRouter, HTTPException

from backend.app.core.logging import get_logger
from backend.app.models.schemas import IngestRequest, IngestResponse
from backend.app.services.blob_service import BlobService
from backend.app.services.pdf_service import PDFService
from backend.app.services.chunk_service import ChunkService
from backend.app.services.embed_service import EmbedService
from backend.app.services.search_service import SearchService

router = APIRouter(prefix="/api", tags=["ingest"])
logger = get_logger(__name__)


@router.post("/ingest", response_model=IngestResponse)
async def ingest_documents(request: IngestRequest) -> IngestResponse:
    """
    Ingest PDFs from Azure Blob Storage into Azure AI Search.
    
    Pipeline:
    1. List and download PDFs from Blob Storage
    2. Extract text from each PDF (page-wise)
    3. Chunk text with overlap
    4. Generate embeddings for each chunk
    5. Index chunks in Azure AI Search
    
    Returns summary of ingestion results.
    """
    logger.info(f"Starting ingestion (force_reindex={request.force_reindex})")
    
    details = []
    num_pdfs = 0
    num_chunks = 0
    num_failures = 0
    
    try:
        blob_service = BlobService()
        pdf_service = PDFService()
        chunk_service = ChunkService()
        embed_service = EmbedService()
        search_service = SearchService(embed_service)
        
        if request.force_reindex:
            try:
                search_service.delete_index()
                details.append("Deleted existing search index")
            except Exception:
                details.append("No existing index to delete")

        search_service.create_or_update_index()
        details.append("Search index created/updated")
        
        documents = blob_service.download_all_pdfs()
        num_pdfs = len(documents)
        details.append(f"Downloaded {num_pdfs} PDFs from blob storage")
        
        if num_pdfs == 0:
            return IngestResponse(
                success=True,
                num_pdfs_processed=0,
                num_chunks_indexed=0,
                num_failures=0,
                message="No PDFs found in blob storage container",
                details=details
            )
        
        all_chunks = []
        for doc in documents:
            try:
                extracted = pdf_service.extract_text(
                    pdf_content=doc.content,
                    filename=doc.filename,
                    source_url=doc.source_url
                )
                
                if not pdf_service.has_extractable_text(extracted):
                    details.append(f"Skipped '{doc.filename}' - no extractable text")
                    num_failures += 1
                    continue
                
                chunks = chunk_service.chunk_document(extracted)
                all_chunks.extend(chunks)
                details.append(f"Processed '{doc.filename}': {len(chunks)} chunks")
                
            except Exception as e:
                logger.error(f"Error processing {doc.filename}: {type(e).__name__}")
                details.append(f"Failed to process '{doc.filename}': {type(e).__name__}")
                num_failures += 1
        
        if not all_chunks:
            return IngestResponse(
                success=True,
                num_pdfs_processed=num_pdfs,
                num_chunks_indexed=0,
                num_failures=num_failures,
                message="No text chunks extracted from PDFs",
                details=details
            )
        
        details.append(f"Generating embeddings for {len(all_chunks)} chunks...")
        chunk_texts = [c.content for c in all_chunks]
        embeddings = embed_service.embed_texts(chunk_texts)
        details.append(f"Generated {len(embeddings)} embeddings")
        
        stats = search_service.index_chunks(all_chunks, embeddings)
        num_chunks = stats.num_succeeded
        
        details.append(f"Indexed {stats.num_succeeded} chunks, {stats.num_failed} failures")
        
        if stats.errors:
            for error in stats.errors[:5]:
                details.append(f"Index error: {error}")
        
        success = num_chunks > 0
        message = (
            f"Successfully ingested {num_pdfs} PDFs with {num_chunks} chunks"
            if success else "Ingestion completed with errors"
        )
        
        logger.info(message)
        
        return IngestResponse(
            success=success,
            num_pdfs_processed=num_pdfs,
            num_chunks_indexed=num_chunks,
            num_failures=num_failures + stats.num_failed,
            message=message,
            details=details
        )
        
    except Exception as e:
        logger.error(f"Ingestion failed: {type(e).__name__}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Ingestion failed: {type(e).__name__}"
        )
