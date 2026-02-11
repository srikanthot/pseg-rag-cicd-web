"""
Azure AI Search service.

Handles index creation, document indexing, and vector/hybrid search queries.
"""

from dataclasses import dataclass
from typing import List, Optional

from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SearchField,
    SearchFieldDataType,
    VectorSearch,
    HnswAlgorithmConfiguration,
    VectorSearchProfile,
    SearchableField,
    SimpleField,
)
from azure.search.documents.models import VectorizedQuery

from backend.app.core.config import settings
from backend.app.core.logging import get_logger
from backend.app.models.schemas import RetrievedChunk, ChunkMetadata
from backend.app.services.chunk_service import DocumentChunk
from backend.app.services.embed_service import EmbedService, EMBEDDING_DIMENSION

logger = get_logger(__name__)


@dataclass
class IndexStats:
    """Statistics about indexing operation."""
    
    num_documents: int
    num_succeeded: int
    num_failed: int
    errors: List[str]


class SearchService:
    """Service for Azure AI Search operations."""
    
    def __init__(self, embed_service: Optional[EmbedService] = None):
        """
        Initialize the search service.
        
        Args:
            embed_service: Optional embedding service for query embedding
        """
        self._credential = AzureKeyCredential(settings.azure_search_api_key)
        self._index_client = SearchIndexClient(
            endpoint=settings.azure_search_endpoint,
            credential=self._credential
        )
        self._search_client: Optional[SearchClient] = None
        self._embed_service = embed_service or EmbedService()
    
    def _get_search_client(self) -> SearchClient:
        """Get or create the search client."""
        if self._search_client is None:
            self._search_client = SearchClient(
                endpoint=settings.azure_search_endpoint,
                index_name=settings.azure_search_index_name,
                credential=self._credential
            )
        return self._search_client
    
    def create_or_update_index(self) -> bool:
        """
        Create or update the search index with vector search configuration.
        
        Returns:
            True if successful
        """
        fields = [
            SimpleField(
                name="id",
                type=SearchFieldDataType.String,
                key=True,
                filterable=True
            ),
            SearchableField(
                name="content",
                type=SearchFieldDataType.String,
                searchable=True
            ),
            SearchField(
                name="contentVector",
                type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                searchable=True,
                vector_search_dimensions=EMBEDDING_DIMENSION,
                vector_search_profile_name="vector-profile"
            ),
            SimpleField(
                name="source_file",
                type=SearchFieldDataType.String,
                filterable=True,
                facetable=True
            ),
            SimpleField(
                name="page_number",
                type=SearchFieldDataType.Int32,
                filterable=True
            ),
            SimpleField(
                name="source_url",
                type=SearchFieldDataType.String,
                filterable=False
            ),
            SimpleField(
                name="chunk_id",
                type=SearchFieldDataType.String,
                filterable=False
            ),
        ]
        
        vector_search = VectorSearch(
            algorithms=[
                HnswAlgorithmConfiguration(name="hnsw-config")
            ],
            profiles=[
                VectorSearchProfile(
                    name="vector-profile",
                    algorithm_configuration_name="hnsw-config"
                )
            ]
        )
        
        index = SearchIndex(
            name=settings.azure_search_index_name,
            fields=fields,
            vector_search=vector_search
        )
        
        try:
            self._index_client.create_or_update_index(index)
            logger.info(f"Index '{settings.azure_search_index_name}' created/updated successfully")
            return True
        except Exception as e:
            logger.error(f"Error creating index: {type(e).__name__}")
            raise
    
    def index_chunks(
        self,
        chunks: List[DocumentChunk],
        embeddings: List[List[float]]
    ) -> IndexStats:
        """
        Index document chunks with their embeddings.
        
        Args:
            chunks: List of document chunks
            embeddings: Corresponding embedding vectors
            
        Returns:
            IndexStats with operation results
        """
        if len(chunks) != len(embeddings):
            raise ValueError("Number of chunks must match number of embeddings")
        
        documents = []
        for chunk, embedding in zip(chunks, embeddings):
            doc = {
                "id": chunk.chunk_id,
                "content": chunk.content,
                "contentVector": embedding,
                "source_file": chunk.source_file,
                "page_number": chunk.page_number,
                "source_url": chunk.source_url,
                "chunk_id": chunk.chunk_id,
            }
            documents.append(doc)
        
        search_client = self._get_search_client()
        errors: List[str] = []
        succeeded = 0
        failed = 0
        
        batch_size = 100
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            try:
                result = search_client.upload_documents(documents=batch)
                for r in result:
                    if r.succeeded:
                        succeeded += 1
                    else:
                        failed += 1
                        errors.append(f"Failed to index {r.key}: {r.error_message}")
            except Exception as e:
                failed += len(batch)
                errors.append(f"Batch upload error: {type(e).__name__}")
                logger.error(f"Error uploading batch: {type(e).__name__}")
        
        logger.info(f"Indexed {succeeded} chunks, {failed} failures")
        
        return IndexStats(
            num_documents=len(chunks),
            num_succeeded=succeeded,
            num_failed=failed,
            errors=errors
        )
    
    def search(
        self,
        query: str,
        top_k: int = 5,
        use_hybrid: bool = True
    ) -> List[RetrievedChunk]:
        """
        Search for relevant chunks using vector and optional hybrid search.
        
        Args:
            query: User's question
            top_k: Number of results to return
            use_hybrid: Whether to use hybrid (vector + keyword) search
            
        Returns:
            List of retrieved chunks with scores
        """
        query_embedding = self._embed_service.embed_text(query)
        
        vector_query = VectorizedQuery(
            vector=query_embedding,
            k_nearest_neighbors=top_k,
            fields="contentVector"
        )
        
        search_client = self._get_search_client()
        
        try:
            if use_hybrid:
                results = search_client.search(
                    search_text=query,
                    vector_queries=[vector_query],
                    top=top_k,
                    select=["id", "content", "source_file", "page_number", "source_url", "chunk_id"]
                )
            else:
                results = search_client.search(
                    search_text=None,
                    vector_queries=[vector_query],
                    top=top_k,
                    select=["id", "content", "source_file", "page_number", "source_url", "chunk_id"]
                )
            
            retrieved_chunks: List[RetrievedChunk] = []
            
            for result in results:
                score = result.get("@search.score", 0.0)
                
                chunk = RetrievedChunk(
                    content=result["content"],
                    score=score,
                    metadata=ChunkMetadata(
                        source_file=result["source_file"],
                        page_number=result["page_number"],
                        chunk_id=result["chunk_id"],
                        source_url=result["source_url"]
                    )
                )
                retrieved_chunks.append(chunk)
            
            logger.info(f"Search returned {len(retrieved_chunks)} results for query")
            return retrieved_chunks
            
        except Exception as e:
            logger.error(f"Search error: {type(e).__name__}: {str(e)}")
            raise
    
    def delete_all_documents(self) -> bool:
        """Delete all documents from the index."""
        try:
            search_client = self._get_search_client()
            results = search_client.search(search_text="*", select=["id"], top=1000)

            doc_ids = [{"id": r["id"]} for r in results]

            if doc_ids:
                search_client.delete_documents(documents=doc_ids)
                logger.info(f"Deleted {len(doc_ids)} documents from index")

            return True
        except Exception as e:
            logger.error(f"Error deleting documents: {type(e).__name__}")
            raise

    def delete_index(self) -> bool:
        """Delete the search index entirely."""
        try:
            self._index_client.delete_index(settings.azure_search_index_name)
            logger.info(f"Index '{settings.azure_search_index_name}' deleted successfully")
            self._search_client = None  # Reset client since index is gone
            return True
        except Exception as e:
            logger.error(f"Error deleting index: {type(e).__name__}: {str(e)}")
            raise
