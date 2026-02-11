# RAG Chatbot

Enterprise-grade Retrieval-Augmented Generation (RAG) chatbot using Azure Blob Storage, Azure AI Search, and Azure OpenAI. Provides grounded responses with citations from PDF documents.

## Features

- PDF document ingestion from Azure Blob Storage
- Vector and hybrid search using Azure AI Search
- Grounded responses using Azure OpenAI
- Strict grounding to prevent hallucinations
- Citations with clickable document links
- Professional Streamlit UI
- FastAPI backend with health endpoints
- Azure App Service deployment ready

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Streamlit UI  │────▶│  FastAPI Backend │────▶│  Azure Services │
│   (Port 8501)   │◀────│   (Port 8000)    │◀────│                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

## Prerequisites

### Azure Resources

1. **Azure OpenAI Service** with deployed models:
   - Chat model (e.g., `gpt-4`, `gpt-35-turbo`)
   - Embedding model (e.g., `text-embedding-ada-002`)

2. **Azure AI Search** service (Basic tier or higher for vector search)

3. **Azure Blob Storage** account with a container for PDF documents

### Local Development

- Python 3.11+
- pip

## Quick Start

### 1. Clone and Setup

```bash
git clone <repository-url>
cd rag-chatbot

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# or
.\.venv\Scripts\Activate.ps1  # Windows

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your Azure credentials
```

Required environment variables:

| Variable | Description |
|----------|-------------|
| `AZURE_OPENAI_ENDPOINT` | Azure OpenAI endpoint URL |
| `AZURE_OPENAI_API_KEY` | Azure OpenAI API key |
| `AZURE_OPENAI_CHAT_DEPLOYMENT` | Chat model deployment name |
| `AZURE_OPENAI_EMBEDDING_DEPLOYMENT` | Embedding model deployment name |
| `AZURE_SEARCH_ENDPOINT` | Azure AI Search endpoint URL |
| `AZURE_SEARCH_API_KEY` | Azure AI Search admin API key |
| `AZURE_STORAGE_CONNECTION_STRING` | Blob Storage connection string |

### 3. Create Search Index

```bash
python scripts/create_search_index.py
```

### 4. Upload PDFs

Upload your PDF documents to the Azure Blob Storage container specified in `AZURE_STORAGE_CONTAINER_NAME` (default: `pdfs`).

### 5. Run the Application

#### Option A: Using the run script

```bash
# Linux/Mac
./scripts/run_local.sh

# Windows
.\scripts\run_local.ps1
```

#### Option B: Manual startup

```bash
# Terminal 1: Start backend
export PYTHONPATH=$(pwd)
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2: Start UI
cd ui
streamlit run streamlit_app.py --server.port 8501
```

### 6. Access the Application

- **Streamlit UI**: http://localhost:8501
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

### 7. Ingest Documents

1. Open the Streamlit UI
2. Click "Ingest PDFs" in the sidebar
3. Wait for ingestion to complete

### 8. Ask Questions

Type your question in the chat input. The system will:
- Search for relevant document chunks
- Generate a grounded response
- Display citations with clickable links

## Project Structure

```
rag-chatbot/
├── backend/
│   ├── app/
│   │   ├── api/           # FastAPI routes
│   │   ├── core/          # Configuration and logging
│   │   ├── models/        # Pydantic schemas
│   │   ├── services/      # Business logic
│   │   └── utils/         # Helpers and utilities
│   └── tests/             # Unit tests
├── ui/
│   ├── components/        # Streamlit components
│   └── streamlit_app.py   # Main UI application
├── docker/                # Dockerfiles
├── scripts/               # Utility scripts
├── infra/                 # Deployment documentation
├── docs/                  # Documentation
├── .env.example           # Environment template
└── requirements.txt       # Python dependencies
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check with config summary |
| `/api/chat` | POST | Process question and return response |
| `/api/ingest` | POST | Trigger document ingestion |

### Chat Request

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the main topic?", "top_k": 5}'
```

### Ingest Request

```bash
curl -X POST http://localhost:8000/api/ingest \
  -H "Content-Type: application/json" \
  -d '{"force_reindex": false}'
```

## Configuration

### RAG Tuning Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `TOP_K` | 5 | Number of chunks to retrieve |
| `SCORE_THRESHOLD` | 0.3 | Minimum relevance score |
| `STRICT_GROUNDING` | true | Enable hallucination prevention |

### Chunking Parameters

Default chunking configuration (in `chunk_service.py`):
- Chunk size: ~1000 characters
- Overlap: 150 characters
- Minimum chunk size: 50 characters

## Deployment

See [infra/appservice_notes.md](infra/appservice_notes.md) for Azure App Service deployment instructions.

### Docker

```bash
# Build images
docker build -f docker/backend.Dockerfile -t rag-chatbot-backend .
docker build -f docker/ui.Dockerfile -t rag-chatbot-ui .

# Run containers
docker run -p 8000:8000 --env-file .env rag-chatbot-backend
docker run -p 8501:8501 -e BACKEND_URL=http://host.docker.internal:8000 rag-chatbot-ui
```

## Troubleshooting

### Missing Environment Variables

```
ValueError: Missing required environment variables: ...
```

Ensure all required variables are set in your `.env` file.

### Empty PDF Text Extraction

```
PDF 'document.pdf' has no extractable text (possibly scanned)
```

The PDF contains scanned images without OCR. Use PDFs with embedded text or run OCR first.

### Search Index Not Found

```
ResourceNotFoundError: The index 'rag-documents' does not exist
```

Run `python scripts/create_search_index.py` to create the index.

### Embedding Dimension Mismatch

Delete the existing index in Azure Portal and recreate it with the correct embedding model.

See [docs/troubleshooting.md](docs/troubleshooting.md) for more solutions.

## Documentation

- [Architecture](docs/architecture.md) - System design and data flow
- [Runbook](docs/runbook.md) - Operational procedures
- [Troubleshooting](docs/troubleshooting.md) - Common issues and solutions
- [Environment Configuration](infra/env_config_notes.md) - All configuration options
- [App Service Deployment](infra/appservice_notes.md) - Azure deployment guide

## Testing

```bash
# Run unit tests
pytest backend/tests/ -v
```

## License

Proprietary - All rights reserved.
