"""
Azure OpenAI embeddings service.

Generates vector embeddings for text chunks using Azure OpenAI.
Includes retry logic for transient failures.
"""

from typing import List
import time

from openai import AzureOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from backend.app.core.config import settings
from backend.app.core.logging import get_logger

logger = get_logger(__name__)

EMBEDDING_DIMENSION = 1536  # text-embedding-ada-002 dimension


class EmbedService:
    """Service for generating text embeddings using Azure OpenAI."""
    
    def __init__(self):
        """Initialize the Azure OpenAI client for embeddings.

        Uses embedding-specific endpoint and API key if configured,
        otherwise falls back to the main Azure OpenAI endpoint.
        """
        self._client = AzureOpenAI(
            azure_endpoint=settings.get_embedding_endpoint(),
            api_key=settings.get_embedding_api_key(),
            api_version=settings.azure_openai_api_version
        )
        self._deployment = settings.azure_openai_embedding_deployment
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((Exception,)),
        before_sleep=lambda retry_state: logger.warning(
            f"Embedding request failed, retrying (attempt {retry_state.attempt_number})"
        )
    )
    def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding vector for a single text.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector as list of floats
        """
        if not text or not text.strip():
            raise ValueError("Cannot embed empty text")
        
        response = self._client.embeddings.create(
            input=text,
            model=self._deployment
        )
        
        return response.data[0].embedding
    
    def embed_texts(
        self,
        texts: List[str],
        batch_size: int = 16
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple texts with batching.
        
        Args:
            texts: List of texts to embed
            batch_size: Number of texts to embed per API call
            
        Returns:
            List of embedding vectors
        """
        if not texts:
            return []
        
        all_embeddings: List[List[float]] = []
        total_batches = (len(texts) + batch_size - 1) // batch_size
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_num = i // batch_size + 1
            
            try:
                response = self._client.embeddings.create(
                    input=batch,
                    model=self._deployment
                )
                
                batch_embeddings = [item.embedding for item in response.data]
                all_embeddings.extend(batch_embeddings)
                
                logger.info(f"Embedded batch {batch_num}/{total_batches} ({len(batch)} texts)")
                
                if i + batch_size < len(texts):
                    time.sleep(0.1)
                    
            except Exception as e:
                logger.error(f"Error embedding batch {batch_num}: {type(e).__name__}")
                raise
        
        return all_embeddings
    
    @staticmethod
    def get_embedding_dimension() -> int:
        """Return the embedding dimension for the configured model."""
        return EMBEDDING_DIMENSION
