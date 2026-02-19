# Azure App Service Deployment Guide

This document provides instructions for deploying the RAG Chatbot to Azure App Service.

## Architecture Overview

The application consists of two components that can be deployed as separate App Services:

1. **Backend API** - FastAPI application serving the RAG endpoints
2. **Streamlit UI** - Web interface for user interaction

## Prerequisites

Before deploying, ensure you have:

1. Azure subscription with the following resources provisioned:
   - Azure OpenAI Service with deployed models (chat + embeddings)
   - Azure AI Search service
   - Azure Blob Storage account with a container for PDFs
   - Azure Container Registry (if using container deployment)

2. Azure CLI installed and authenticated

3. Docker installed (for container builds)

## Deployment Options

### Option 1: Container Deployment (Recommended)

Build and push Docker images to Azure Container Registry, then deploy to App Service.

#### Step 1: Build Docker Images

```bash
# From project root
docker build -f docker/backend.Dockerfile -t rag-chatbot-backend:latest .
docker build -f docker/ui.Dockerfile -t rag-chatbot-ui:latest .
```

#### Step 2: Push to Azure Container Registry

```bash
# Login to ACR
az acr login --name <your-acr-name>

# Tag images
docker tag rag-chatbot-backend:latest <your-acr-name>.azurecr.io/rag-chatbot-backend:latest
docker tag rag-chatbot-ui:latest <your-acr-name>.azurecr.io/rag-chatbot-ui:latest

# Push images
docker push <your-acr-name>.azurecr.io/rag-chatbot-backend:latest
docker push <your-acr-name>.azurecr.io/rag-chatbot-ui:latest
```

#### Step 3: Create App Services

```bash
# Create App Service Plan
az appservice plan create \
    --name rag-chatbot-plan \
    --resource-group <your-rg> \
    --sku B2 \
    --is-linux

# Create Backend App Service
az webapp create \
    --name rag-chatbot-backend \
    --resource-group <your-rg> \
    --plan rag-chatbot-plan \
    --deployment-container-image-name <your-acr-name>.azurecr.io/rag-chatbot-backend:latest

# Create UI App Service
az webapp create \
    --name rag-chatbot-ui \
    --resource-group <your-rg> \
    --plan rag-chatbot-plan \
    --deployment-container-image-name <your-acr-name>.azurecr.io/rag-chatbot-ui:latest
```

### Option 2: Code Deployment

Deploy directly from source code using ZIP deployment.

```bash
# Backend
cd backend
zip -r ../backend.zip .
az webapp deployment source config-zip \
    --resource-group <your-rg> \
    --name rag-chatbot-backend \
    --src ../backend.zip

# UI
cd ../ui
zip -r ../ui.zip .
az webapp deployment source config-zip \
    --resource-group <your-rg> \
    --name rag-chatbot-ui \
    --src ../ui.zip
```

## Required App Settings

Configure these environment variables in Azure App Service Configuration:

### Backend App Service

| Setting | Description | Example |
|---------|-------------|---------|
| `AZURE_OPENAI_ENDPOINT` | Azure OpenAI endpoint URL | `https://myopenai.openai.azure.com/` |
| `AZURE_OPENAI_API_KEY` | Azure OpenAI API key | `abc123...` |
| `AZURE_OPENAI_API_VERSION` | API version | `2024-02-15-preview` |
| `AZURE_OPENAI_CHAT_DEPLOYMENT` | Chat model deployment name | `gpt-4` |
| `AZURE_OPENAI_EMBEDDING_DEPLOYMENT` | Embedding model deployment | `text-embedding-ada-002` |
| `AZURE_SEARCH_ENDPOINT` | Azure AI Search endpoint | `https://mysearch.search.windows.net` |
| `AZURE_SEARCH_API_KEY` | Azure AI Search API key | `xyz789...` |
| `AZURE_SEARCH_INDEX_NAME` | Search index name | `rag-documents` |
| `AZURE_STORAGE_CONNECTION_STRING` | Blob storage connection string | `DefaultEndpointsProtocol=https;...` |
| `AZURE_STORAGE_CONTAINER_NAME` | Container name for PDFs | `pdfs` |
| `BLOB_BASE_URL` | Base URL for blob links | `https://mystorage.blob.core.windows.net/pdfs` |
| `TOP_K` | Default number of results | `5` |
| `SCORE_THRESHOLD` | Confidence threshold | `0.3` |
| `STRICT_GROUNDING` | Enable strict grounding | `true` |

### UI App Service

| Setting | Description | Example |
|---------|-------------|---------|
| `BACKEND_URL` | URL of the backend App Service | `https://rag-chatbot-backend.azurewebsites.net` |

## Startup Commands

### Backend

For container deployment, the Dockerfile CMD is used. For code deployment:

```bash
gunicorn -k uvicorn.workers.UvicornWorker backend.app.main:app --bind 0.0.0.0:8000 --workers 2 --timeout 120
```

### UI

For container deployment, the Dockerfile CMD is used. For code deployment:

```bash
streamlit run streamlit_app.py --server.port=8501 --server.address=0.0.0.0 --server.headless=true
```

## Health Endpoint

The backend exposes a `/health` endpoint that returns:

```json
{
    "status": "ok",
    "version": "1.0.0",
    "config_summary": {
        "azure_search_index_name": "rag-documents",
        "azure_openai_chat_deployment": "gpt-4",
        ...
    }
}
```

Configure App Service health check to use this endpoint:

```bash
az webapp config set \
    --resource-group <your-rg> \
    --name rag-chatbot-backend \
    --generic-configurations '{"healthCheckPath": "/health"}'
```

## Networking Considerations

1. **CORS**: The backend allows all origins by default. For production, restrict to your UI domain.

2. **VNET Integration**: For enhanced security, deploy both services in a VNET with private endpoints for Azure services.

3. **Authentication**: Consider adding Azure AD authentication for production use.

## Scaling

The application is stateless and can be scaled horizontally:

```bash
az appservice plan update \
    --name rag-chatbot-plan \
    --resource-group <your-rg> \
    --number-of-workers 3
```

## Monitoring

Enable Application Insights for monitoring:

```bash
az webapp config appsettings set \
    --resource-group <your-rg> \
    --name rag-chatbot-backend \
    --settings APPLICATIONINSIGHTS_CONNECTION_STRING="<your-connection-string>"
```

## Troubleshooting

1. **Container not starting**: Check container logs in Azure Portal or via CLI
2. **Environment variables not loading**: Verify App Settings are configured correctly
3. **Health check failing**: Ensure the backend can connect to all Azure services
4. **Slow responses**: Consider upgrading the App Service Plan or optimizing TOP_K
