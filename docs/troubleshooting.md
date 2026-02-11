# Troubleshooting Guide

This guide helps diagnose and resolve common issues with the RAG Chatbot application.

## Startup Issues

### Missing Environment Variables

**Symptom**: Application fails to start with error about missing variables.

**Error**:
```
ValueError: Missing required environment variables: AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY, ...
```

**Solution**:
1. Copy `.env.example` to `.env`
2. Fill in all required values
3. Ensure the `.env` file is in the project root directory
4. Restart the application

### Invalid Endpoint URL

**Symptom**: Validation error on startup.

**Error**:
```
ValueError: Endpoint URL must start with https://
```

**Solution**:
Ensure your endpoint URLs include the `https://` prefix:
```
AZURE_OPENAI_ENDPOINT=https://myresource.openai.azure.com/
AZURE_SEARCH_ENDPOINT=https://mysearch.search.windows.net
```

### Module Not Found

**Symptom**: Import errors when starting the application.

**Error**:
```
ModuleNotFoundError: No module named 'backend'
```

**Solution**:
1. Ensure you're running from the project root
2. Set PYTHONPATH: `export PYTHONPATH=/path/to/project`
3. Or use the provided run scripts: `./scripts/run_local.sh`

## Connection Issues

### Cannot Connect to Azure OpenAI

**Symptom**: Embedding or chat completion fails.

**Error**:
```
openai.AuthenticationError: Incorrect API key provided
```

**Solution**:
1. Verify `AZURE_OPENAI_API_KEY` is correct
2. Check the key hasn't expired
3. Ensure the endpoint matches your Azure OpenAI resource
4. Verify the deployment names are correct

### Cannot Connect to Azure AI Search

**Symptom**: Search or indexing fails.

**Error**:
```
azure.core.exceptions.HttpResponseError: (401) Access denied
```

**Solution**:
1. Verify `AZURE_SEARCH_API_KEY` is correct (use admin key, not query key)
2. Check the endpoint URL is correct
3. Ensure the search service is running

### Cannot Connect to Azure Blob Storage

**Symptom**: PDF download fails.

**Error**:
```
azure.core.exceptions.ClientAuthenticationError: Server failed to authenticate the request
```

**Solution**:
1. Verify the connection string is complete and correct
2. Check the storage account is accessible
3. Ensure the container exists and has PDFs

## Ingestion Issues

### No PDFs Found

**Symptom**: Ingestion completes but reports 0 PDFs.

**Cause**: Container is empty or files don't have `.pdf` extension.

**Solution**:
1. Upload PDF files to the configured container
2. Ensure files have `.pdf` extension (case-insensitive)
3. Verify `AZURE_STORAGE_CONTAINER_NAME` is correct

### Empty PDF Text Extraction

**Symptom**: PDFs are processed but no chunks are created.

**Log**:
```
PDF 'document.pdf' has no extractable text (possibly scanned)
```

**Cause**: PDF contains scanned images without OCR text layer.

**Solution**:
1. Use PDFs with embedded text (not scanned images)
2. Run OCR on scanned PDFs before uploading
3. Consider using Azure Document Intelligence for OCR

### Embedding Dimension Mismatch

**Symptom**: Indexing fails with dimension error.

**Error**:
```
The dimension of the vector field 'contentVector' does not match
```

**Cause**: Index was created with different embedding model.

**Solution**:
1. Delete the existing index in Azure Portal
2. Run `python scripts/create_search_index.py`
3. Re-ingest documents

### Index Not Found

**Symptom**: Search fails because index doesn't exist.

**Error**:
```
azure.core.exceptions.ResourceNotFoundError: The index 'rag-documents' does not exist
```

**Solution**:
1. Run `python scripts/create_search_index.py`
2. Or trigger ingestion which creates the index automatically

## Query Issues

### All Questions Return Out-of-Context

**Symptom**: Every question gets "outside the provided documents" response.

**Possible Causes**:
1. No documents indexed
2. Score threshold too high
3. Documents don't contain relevant information

**Solutions**:
1. Check ingestion completed successfully
2. Lower `SCORE_THRESHOLD` (try 0.1)
3. Verify documents contain relevant content
4. Check search index has documents:
   ```bash
   curl "http://localhost:8000/health"
   ```

### Slow Response Times

**Symptom**: Queries take more than 10 seconds.

**Possible Causes**:
1. Large `TOP_K` value
2. Azure service throttling
3. Network latency

**Solutions**:
1. Reduce `TOP_K` to 3-5
2. Check Azure service quotas
3. Consider upgrading Azure service tiers

### Citations Not Showing

**Symptom**: Answers appear but no citations displayed.

**Possible Causes**:
1. UI rendering issue
2. Backend not returning citations

**Solutions**:
1. Check browser console for errors
2. Test API directly:
   ```bash
   curl -X POST http://localhost:8000/api/chat \
     -H "Content-Type: application/json" \
     -d '{"question": "test question"}'
   ```
3. Verify response includes `citations` array

## UI Issues

### Cannot Connect to Backend

**Symptom**: UI shows "Backend offline" in sidebar.

**Solution**:
1. Ensure backend is running on port 8000
2. Check `BACKEND_URL` environment variable
3. Verify no firewall blocking the connection

### Chat History Lost on Refresh

**Symptom**: Refreshing the page clears chat history.

**Explanation**: This is expected behavior. Chat history is stored in Streamlit session state which is cleared on page refresh.

**Workaround**: Don't refresh the page during a session.

### Streamlit Errors

**Symptom**: Streamlit shows error messages.

**Common Errors**:
- `StreamlitAPIException`: Usually a code issue
- `ConnectionError`: Backend not reachable

**Solution**:
1. Check Streamlit logs in terminal
2. Restart Streamlit: `streamlit run ui/streamlit_app.py`

## Docker Issues

### Container Won't Start

**Symptom**: Docker container exits immediately.

**Solution**:
1. Check container logs: `docker logs <container-id>`
2. Verify all environment variables are passed
3. Ensure ports are not already in use

### Health Check Failing

**Symptom**: Container marked unhealthy.

**Solution**:
1. Check if the application started successfully
2. Verify the health endpoint is accessible inside container
3. Increase health check start period if startup is slow

## Getting Help

If you've tried the solutions above and still have issues:

1. Check application logs for detailed error messages
2. Verify all Azure services are running and accessible
3. Test each Azure service independently
4. Review the architecture documentation
5. Contact support with:
   - Error messages (with secrets redacted)
   - Steps to reproduce
   - Environment details (OS, Python version, etc.)
