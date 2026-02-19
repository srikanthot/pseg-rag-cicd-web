"""
RAG orchestration service.

Coordinates retrieval, grounding checks, and response generation
with strict citation requirements.
"""

from typing import List, Optional

from openai import AzureOpenAI

from backend.app.core.config import settings
from backend.app.core.logging import get_logger
from backend.app.models.schemas import (
    ChatResponse,
    Citation,
    ConversationMessage,
    RetrievedChunk,
)
from backend.app.services.search_service import SearchService
from backend.app.services.embed_service import EmbedService
from backend.app.services.blob_service import BlobService
from backend.app.utils.thresholds import (
    check_retrieval_quality,
    OUT_OF_CONTEXT_MESSAGE,
    GatingResult,
)
from backend.app.utils.text import truncate_text

logger = get_logger(__name__)

SYSTEM_PROMPT = """You are a helpful assistant that answers questions based ONLY on the provided source documents.

IMPORTANT RULES:
1. Answer ONLY using information from the provided sources below.
2. If the sources don't contain relevant information to answer the question, say "I don't have enough information in the provided documents to answer this question."
3. Always cite your sources by referencing the document name and page number.
4. Be concise and accurate.
5. Do not make up information or use knowledge outside the provided sources.

SOURCES:
{sources}

Answer the user's question based solely on the sources above."""

QUERY_REWRITE_PROMPT = """Given the conversation history below, rewrite the user's latest question to be a standalone question that includes all necessary context. If the question references something from the conversation (like "it", "that", "this", "the above"), replace those references with the actual topic being discussed.

Conversation History:
{history}

Latest Question: {question}

Rewritten standalone question (output ONLY the rewritten question, nothing else):"""


class RAGService:
    """Service for RAG-based question answering."""

    def __init__(
        self,
        search_service: Optional[SearchService] = None,
        embed_service: Optional[EmbedService] = None,
        blob_service: Optional[BlobService] = None
    ):
        """
        Initialize the RAG service.

        Args:
            search_service: Optional search service instance
            embed_service: Optional embedding service instance
            blob_service: Optional blob service instance for SAS URL generation
        """
        self._embed_service = embed_service or EmbedService()
        self._search_service = search_service or SearchService(self._embed_service)
        self._blob_service = blob_service or BlobService()
        self._openai_client = AzureOpenAI(
            azure_endpoint=settings.azure_openai_endpoint,
            api_key=settings.azure_openai_api_key,
            api_version=settings.azure_openai_api_version
        )
        self._chat_deployment = settings.azure_openai_chat_deployment
    
    def _rewrite_query_with_context(
        self,
        question: str,
        conversation_history: List[ConversationMessage]
    ) -> str:
        """Rewrite a follow-up question to include context from conversation history."""
        # Format conversation history for the prompt
        history_text = ""
        for msg in conversation_history[-6:]:  # Limit to last 6 messages
            role = "User" if msg.role == "user" else "Assistant"
            history_text += f"{role}: {msg.content}\n"

        prompt = QUERY_REWRITE_PROMPT.format(history=history_text, question=question)

        try:
            response = self._openai_client.chat.completions.create(
                model=self._chat_deployment,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                max_tokens=200
            )
            rewritten = response.choices[0].message.content.strip()
            logger.info(f"Rewrote query: '{question}' -> '{rewritten}'")
            return rewritten
        except Exception as e:
            logger.warning(f"Query rewrite failed: {type(e).__name__}, using original query")
            return question

    def _format_sources_for_prompt(self, chunks: List[RetrievedChunk]) -> str:
        """Format retrieved chunks as sources for the system prompt."""
        sources = []
        for i, chunk in enumerate(chunks, 1):
            page_info = f"Page: {chunk.metadata.page_number}" if chunk.metadata.page_number else "Page: N/A"
            source_text = (
                f"[Source {i}]\n"
                f"Document: {chunk.metadata.source_file}\n"
                f"{page_info}\n"
                f"Content: {chunk.content}\n"
            )
            sources.append(source_text)
        return "\n---\n".join(sources)
    
    def _build_citations(self, chunks: List[RetrievedChunk]) -> List[Citation]:
        """Build citation objects from retrieved chunks with fresh SAS URLs."""
        citations = []
        seen = set()

        for chunk in chunks:
            key = (chunk.metadata.source_file, chunk.metadata.page_number)
            if key in seen:
                continue
            seen.add(key)

            # Generate fresh SAS URL for secure access
            try:
                base_url = self._blob_service.generate_sas_url(chunk.metadata.source_file)
                # Add PDF open parameters for direct page navigation
                # Using multiple formats for better browser compatibility
                page_num = chunk.metadata.page_number
                # Format: #page=X&view=FitH (works in Chrome, Edge, Firefox)
                if page_num is not None:
                    source_url = f"{base_url}#page={page_num}&view=FitH,top"
                else:
                    source_url = base_url
            except Exception as e:
                logger.warning(f"Failed to generate SAS URL for {chunk.metadata.source_file}: {e}")
                source_url = chunk.metadata.source_url  # Fallback to stored URL

            citations.append(Citation(
                source_file=chunk.metadata.source_file,
                page_number=chunk.metadata.page_number,
                source_url=source_url,
                snippet=truncate_text(chunk.content, max_length=200)
            ))

        return citations
    
    def _generate_response(
        self,
        question: str,
        chunks: List[RetrievedChunk],
        conversation_history: Optional[List[ConversationMessage]] = None
    ) -> str:
        """Generate a response using Azure OpenAI chat model."""
        sources_text = self._format_sources_for_prompt(chunks)
        system_message = SYSTEM_PROMPT.format(sources=sources_text)

        # Build messages list with conversation history
        messages = [{"role": "system", "content": system_message}]

        # Add conversation history if provided (limit to last 10 messages to avoid token limits)
        if conversation_history:
            history_limit = min(len(conversation_history), 10)
            for msg in conversation_history[-history_limit:]:
                messages.append({"role": msg.role, "content": msg.content})

        # Add current question
        messages.append({"role": "user", "content": question})

        try:
            response = self._openai_client.chat.completions.create(
                model=self._chat_deployment,
                messages=messages,
                temperature=0.1,
                max_tokens=1000
            )

            return response.choices[0].message.content or ""

        except Exception as e:
            logger.error(f"Error generating response: {type(e).__name__}")
            raise
    
    def answer_question(
        self,
        question: str,
        top_k: Optional[int] = None,
        conversation_history: Optional[List[ConversationMessage]] = None
    ) -> ChatResponse:
        """
        Answer a question using RAG with strict grounding.

        Args:
            question: User's question
            top_k: Number of chunks to retrieve (overrides default)
            conversation_history: Previous conversation messages for context

        Returns:
            ChatResponse with answer, citations, and metadata
        """
        effective_top_k = top_k or settings.top_k

        logger.info(f"Processing question with top_k={effective_top_k}")

        # Rewrite query if there's conversation history to include context
        search_query = question
        if conversation_history and len(conversation_history) > 0:
            search_query = self._rewrite_query_with_context(question, conversation_history)

        try:
            chunks = self._search_service.search(
                query=search_query,
                top_k=effective_top_k,
                use_hybrid=True
            )
        except Exception as e:
            logger.error(f"Search failed: {type(e).__name__}")
            return ChatResponse(
                answer="An error occurred while searching the documents. Please try again.",
                citations=[],
                out_of_context=True,
                retrieved_chunks_count=0
            )
        
        gating_result = check_retrieval_quality(
            chunks=chunks,
            score_threshold=settings.score_threshold,
            strict_grounding=settings.strict_grounding
        )
        
        if not gating_result.passed:
            logger.info(f"Gating check failed: {gating_result.reason}")
            return ChatResponse(
                answer=OUT_OF_CONTEXT_MESSAGE,
                citations=[],
                out_of_context=True,
                retrieved_chunks_count=gating_result.num_chunks
            )
        
        try:
            answer = self._generate_response(question, chunks, conversation_history)
        except Exception as e:
            logger.error(f"Response generation failed: {type(e).__name__}")
            return ChatResponse(
                answer="An error occurred while generating the response. Please try again.",
                citations=[],
                out_of_context=False,
                retrieved_chunks_count=len(chunks)
            )
        
        citations = self._build_citations(chunks)
        
        logger.info(
            f"Generated response with {len(citations)} citations "
            f"from {len(chunks)} chunks"
        )
        
        return ChatResponse(
            answer=answer,
            citations=citations,
            out_of_context=False,
            retrieved_chunks_count=len(chunks)
        )
