# RAG Chatbot Runbook

This runbook provides operational procedures for the RAG Chatbot application.

## Quick Start

### Prerequisites

1. Python 3.11+
2. Azure subscription with:
   - Azure OpenAI Service (with chat and embedding deployments)
   - Azure AI Search service
   - Azure Blob Storage account

### Local Setup

```bash
# Clone repository
git clone <repository-url>
cd rag-chatbot

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# or
.\.venv\Scripts\Activate.ps1  # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your Azure credentials

# Create search index
python scripts/create_search_index.py

# Upload PDFs to Azure Blob Storage container

# Start the application
./scripts/run_local.sh  # Linux/Mac
# or
.\scripts\run_local.ps1  # Windows
```

### Access Points

- **Streamlit UI**: http://localhost:8501
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## Common Operations

### Ingesting Documents

#### Via UI

1. Open Streamlit UI at http://localhost:8501
2. In the sidebar, click "Ingest PDFs"
3. Wait for completion and review the summary

#### Via API

```bash
curl -X POST http://localhost:8000/api/ingest \
  -H "Content-Type: application/json" \
  -d '{"force_reindex": false}'
```

#### Force Re-indexing

To delete existing index and re-process all documents:

```bash
curl -X POST http://localhost:8000/api/ingest \
  -H "Content-Type: application/json" \
  -d '{"force_reindex": true}'
```

### Asking Questions

#### Via UI

1. Type your question in the chat input
2. View the response with citations
3. Click citation links to open source documents

#### Via API

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the main topic of the documents?", "top_k": 5}'
```

### Health Check

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "ok",
  "version": "1.0.0",
  "config_summary": {...}
}
```

## Configuration Tuning

### Adjusting Retrieval

| Parameter | Effect | Recommendation |
|-----------|--------|----------------|
| `TOP_K` | More chunks = more context but slower | Start with 5, increase if answers lack detail |
| `SCORE_THRESHOLD` | Higher = stricter matching | 0.3 is balanced; increase if too many false positives |
| `STRICT_GROUNDING` | Enable/disable gating | Keep enabled for production |

### Chunking Parameters

Edit `backend/app/services/chunk_service.py`:

| Parameter | Default | Effect |
|-----------|---------|--------|
| `chunk_size` | 1000 | Larger chunks = more context per chunk |
| `chunk_overlap` | 150 | More overlap = better continuity |
| `min_chunk_size` | 50 | Filters out tiny fragments |

## Monitoring

### Logs

The application logs to stdout with the format:
```
YYYY-MM-DD HH:MM:SS | LEVEL    | module | message
```

Key log events:
- `Starting ingestion` - Ingestion pipeline started
- `Downloaded X PDFs` - Blob download complete
- `Chunked 'filename': X chunks` - Document processed
- `Indexed X chunks` - Search index updated
- `Search returned X results` - Query executed
- `Gating check failed` - Out-of-context detected

### Metrics to Monitor

1. **Ingestion**
   - Number of PDFs processed
   - Number of chunks indexed
   - Failure count

2. **Queries**
   - Response time
   - Out-of-context rate
   - Average retrieval score

## Backup and Recovery

### Index Backup

Azure AI Search indexes can be recreated from source documents. To backup:

1. Ensure PDFs are backed up in Azure Blob Storage
2. Document the index configuration

### Recovery Procedure

1. Verify Azure services are accessible
2. Run `python scripts/create_search_index.py`
3. Trigger ingestion via UI or API
4. Verify with a test query

## Security Operations

### Rotating API Keys

1. Generate new keys in Azure Portal
2. Update `.env` file or App Service settings
3. Restart the application
4. Verify health endpoint returns OK
5. Revoke old keys

### Audit Logging

The application logs all operations without exposing secrets. For compliance:

1. Enable Azure Monitor for App Service
2. Configure log retention policies
3. Set up alerts for error patterns

## Scaling Operations

### Horizontal Scaling

Both backend and UI are stateless and can be scaled:

```bash
# Azure App Service
az appservice plan update \
  --name <plan-name> \
  --resource-group <rg> \
  --number-of-workers 3
```

### Vertical Scaling

For larger document sets or faster responses:

1. Upgrade Azure OpenAI tier for higher rate limits
2. Upgrade Azure AI Search tier for more replicas
3. Upgrade App Service plan for more CPU/memory

## Maintenance Windows

### Recommended Schedule

| Task | Frequency | Duration |
|------|-----------|----------|
| Re-index documents | Weekly or on document update | 5-30 min |
| Rotate API keys | Monthly | 5 min |
| Review logs | Daily | 10 min |
| Update dependencies | Monthly | 30 min |

### Update Procedure

1. Create a backup of current deployment
2. Test updates in staging environment
3. Deploy during low-traffic period
4. Monitor health endpoint
5. Rollback if issues detected
