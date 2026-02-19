#!/usr/bin/env python3
"""
Script to create or update the Azure AI Search index.

Run this script before ingesting documents to ensure the index exists
with the correct schema and vector search configuration.

Usage:
    python scripts/create_search_index.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv()

from backend.app.core.config import settings
from backend.app.core.logging import get_logger
from backend.app.services.embed_service import EmbedService
from backend.app.services.search_service import SearchService

logger = get_logger(__name__)


def main():
    """Create or update the search index."""
    print("=" * 60)
    print("Azure AI Search Index Setup")
    print("=" * 60)
    
    print(f"\nConfiguration:")
    print(f"  Search Endpoint: {settings.azure_search_endpoint}")
    print(f"  Index Name: {settings.azure_search_index_name}")
    print(f"  Embedding Model: {settings.azure_openai_embedding_deployment}")
    print(f"  Embedding Dimension: {EmbedService.get_embedding_dimension()}")
    
    print("\nCreating/updating index...")
    
    try:
        embed_service = EmbedService()
        search_service = SearchService(embed_service)
        
        success = search_service.create_or_update_index()
        
        if success:
            print("\nIndex created/updated successfully!")
            print(f"\nNext steps:")
            print(f"  1. Upload PDFs to Azure Blob Storage container: {settings.azure_storage_container_name}")
            print(f"  2. Run the ingestion endpoint or use the UI to ingest documents")
            print(f"  3. Start asking questions!")
        else:
            print("\nFailed to create index.")
            sys.exit(1)
            
    except Exception as e:
        print(f"\nError: {type(e).__name__}: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
