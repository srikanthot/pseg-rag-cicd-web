# RAG Chatbot Architecture

This document describes the architecture of the enterprise-grade RAG Chatbot application.

## System Overview

The RAG Chatbot is a document question-answering system that uses Retrieval-Augmented Generation (RAG) to provide grounded responses from PDF documents stored in Azure Blob Storage.

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Streamlit UI  │────▶│  FastAPI Backend │────▶│  Azure Services │
│   (Port 8501)   │◀────│   (Port 8000)    │◀────│                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                                        │
                              ┌─────────────────────────┼─────────────────────────┐
                              │                         │                         │
                              ▼                         ▼                         ▼
                    ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
                    │  Azure Blob     │     │  Azure AI       │     │  Azure OpenAI   │
                    │  Storage        │     │  Search         │     │  Service        │
                    │  (PDFs)         │     │  (Vector Index) │     │  (LLM + Embed)  │
                    └─────────────────┘     └─────────────────┘     └─────────────────┘
```

## Components

### Frontend (Streamlit UI)

The user interface is built with Streamlit and provides:

- Chat interface for asking questions
- Citation display with clickable document links
- Sidebar controls for configuration
- Document ingestion trigger
- System health status display

Location: `ui/streamlit_app.py`

### Backend (FastAPI)

The backend API handles all business logic:

- `/api/chat` - Process questions and return grounded responses
- `/api/ingest` - Trigger document ingestion pipeline
- `/health` - Health check endpoint

Location: `backend/app/`

### Services Layer

The application uses a service-oriented architecture:

| Service | Responsibility |
|---------|----------------|
| `BlobService` | List and download PDFs from Azure Blob Storage |
| `PDFService` | Extract text from PDFs page by page |
| `ChunkService` | Split text into overlapping chunks |
| `EmbedService` | Generate embeddings using Azure OpenAI |
| `SearchService` | Manage Azure AI Search index and queries |
| `RAGService` | Orchestrate retrieval and response generation |

## Data Flow

### Ingestion Pipeline

```
1. BlobService.download_all_pdfs()
   └── Downloads PDFs from Azure Blob Storage

2. PDFService.extract_text()
   └── Extracts text per page using PyMuPDF

3. ChunkService.chunk_document()
   └── Splits text into ~1000 char chunks with 150 char overlap

4. EmbedService.embed_texts()
   └── Generates 1536-dim vectors via Azure OpenAI

5. SearchService.index_chunks()
   └── Uploads chunks + vectors to Azure AI Search
```

### Query Pipeline

```
1. User submits question via UI

2. SearchService.search()
   ├── Embed question using EmbedService
   └── Hybrid search (vector + keyword) in Azure AI Search

3. check_retrieval_quality()
   ├── If no results or score < threshold → OUT_OF_CONTEXT
   └── If passed → continue to generation

4. RAGService._generate_response()
   ├── Build system prompt with retrieved sources
   └── Call Azure OpenAI chat completion

5. Return response with citations to UI
```

## Strict Grounding

The application implements strict grounding to prevent hallucinations:

1. **Retrieval Gating**: If no documents are retrieved or the top score is below the threshold, the system returns an out-of-context message without calling the LLM.

2. **System Prompt**: The LLM is instructed to only use provided sources and admit when information is not available.

3. **Citation Requirement**: Every response includes citations with document name, page number, and clickable link.

## Search Index Schema

The Azure AI Search index uses the following schema:

| Field | Type | Purpose |
|-------|------|---------|
| `id` | String (Key) | Unique chunk identifier |
| `content` | String (Searchable) | Chunk text content |
| `contentVector` | Vector (1536 dims) | Embedding for vector search |
| `source_file` | String (Filterable) | Original PDF filename |
| `page_number` | Int32 (Filterable) | Page number in PDF |
| `source_url` | String | Clickable document URL |
| `chunk_id` | String | Chunk identifier |

## Security Considerations

1. **Secret Management**: API keys are loaded from environment variables, never logged
2. **Secret Filtering**: Logging includes a filter to redact potential secrets
3. **CORS**: Configured for development; restrict in production
4. **Input Validation**: Pydantic models validate all API inputs

## Scalability

The application is designed for horizontal scaling:

- **Stateless Backend**: No session state stored in the backend
- **Stateless UI**: Chat history stored in Streamlit session state
- **Azure Services**: All Azure services scale independently

## Error Handling

The application handles errors gracefully:

- Connection failures return user-friendly messages
- Ingestion failures are logged with details
- Search failures trigger out-of-context response
- All errors are logged without exposing secrets
