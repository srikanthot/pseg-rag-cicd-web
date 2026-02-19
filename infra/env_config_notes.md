# Environment Configuration Guide

This document explains all configuration options for the RAG Chatbot application.

## Configuration Sources

The application loads configuration from environment variables. For local development, use a `.env` file in the project root.

## Required Configuration

These variables must be set for the application to start:

### Azure OpenAI

| Variable | Description | Example |
|----------|-------------|---------|
| `AZURE_OPENAI_ENDPOINT` | Your Azure OpenAI resource endpoint | `https://myresource.openai.azure.com/` |
| `AZURE_OPENAI_API_KEY` | API key for Azure OpenAI | `abc123def456...` |
| `AZURE_OPENAI_CHAT_DEPLOYMENT` | Name of your chat model deployment | `gpt-4`, `gpt-35-turbo` |
| `AZURE_OPENAI_EMBEDDING_DEPLOYMENT` | Name of your embedding model deployment | `text-embedding-ada-002` |

### Azure AI Search

| Variable | Description | Example |
|----------|-------------|---------|
| `AZURE_SEARCH_ENDPOINT` | Your Azure AI Search service endpoint | `https://mysearch.search.windows.net` |
| `AZURE_SEARCH_API_KEY` | Admin API key for Azure AI Search | `xyz789abc...` |

### Azure Blob Storage

| Variable | Description | Example |
|----------|-------------|---------|
| `AZURE_STORAGE_CONNECTION_STRING` | Full connection string for storage account | `DefaultEndpointsProtocol=https;AccountName=...` |

## Optional Configuration

These variables have sensible defaults but can be customized:

### Azure OpenAI

| Variable | Default | Description |
|----------|---------|-------------|
| `AZURE_OPENAI_API_VERSION` | `2024-02-15-preview` | Azure OpenAI API version |

### Azure AI Search

| Variable | Default | Description |
|----------|---------|-------------|
| `AZURE_SEARCH_INDEX_NAME` | `rag-documents` | Name of the search index |

### Azure Blob Storage

| Variable | Default | Description |
|----------|---------|-------------|
| `AZURE_STORAGE_CONTAINER_NAME` | `pdfs` | Container name for PDF documents |
| `BLOB_BASE_URL` | Auto-generated | Base URL for building clickable document links |

### RAG Tuning

| Variable | Default | Description |
|----------|---------|-------------|
| `TOP_K` | `5` | Number of document chunks to retrieve per query |
| `SCORE_THRESHOLD` | `0.3` | Minimum relevance score for retrieval results |
| `STRICT_GROUNDING` | `true` | Enable strict grounding to prevent hallucinations |

### Application

| Variable | Default | Description |
|----------|---------|-------------|
| `BACKEND_HOST` | `0.0.0.0` | Host to bind the backend server |
| `BACKEND_PORT` | `8000` | Port for the backend server |
| `LOG_LEVEL` | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL) |

### UI Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `BACKEND_URL` | `http://localhost:8000` | URL of the backend API |

## Configuration Validation

The application validates configuration at startup:

1. **Required variables**: Application fails to start if any required variable is missing
2. **URL format**: Endpoint URLs must start with `https://`
3. **Numeric ranges**: `TOP_K` must be 1-20, `SCORE_THRESHOLD` must be 0.0-1.0
4. **Log level**: Must be a valid Python logging level

## Security Best Practices

1. **Never commit `.env` files** - The `.gitignore` excludes them by default
2. **Use Azure Key Vault** in production for secret management
3. **Rotate API keys** regularly
4. **Use managed identities** when possible instead of API keys
5. **Restrict network access** to Azure services using private endpoints

## Example .env File

```bash
# Azure OpenAI
AZURE_OPENAI_ENDPOINT=https://myopenai.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key-here
AZURE_OPENAI_API_VERSION=2024-02-15-preview
AZURE_OPENAI_CHAT_DEPLOYMENT=gpt-4
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-ada-002

# Azure AI Search
AZURE_SEARCH_ENDPOINT=https://mysearch.search.windows.net
AZURE_SEARCH_API_KEY=your-search-api-key
AZURE_SEARCH_INDEX_NAME=rag-documents

# Azure Blob Storage
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=mystorage;AccountKey=...;EndpointSuffix=core.windows.net
AZURE_STORAGE_CONTAINER_NAME=pdfs
BLOB_BASE_URL=https://mystorage.blob.core.windows.net/pdfs

# RAG Tuning
TOP_K=5
SCORE_THRESHOLD=0.3
STRICT_GROUNDING=true

# Logging
LOG_LEVEL=INFO
```

## Troubleshooting Configuration Issues

### Missing Required Variables

Error: `Missing required environment variables: AZURE_OPENAI_ENDPOINT, ...`

Solution: Ensure all required variables are set in your `.env` file or environment.

### Invalid Endpoint URL

Error: `Endpoint URL must start with https://`

Solution: Check that your endpoint URLs include the `https://` prefix.

### Connection Failures

If the application starts but fails to connect to Azure services:

1. Verify API keys are correct and not expired
2. Check network connectivity to Azure endpoints
3. Ensure Azure services are provisioned and running
4. Verify the connection string format for Blob Storage
