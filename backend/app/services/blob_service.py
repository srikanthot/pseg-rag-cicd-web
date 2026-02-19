"""
Azure Blob Storage service for PDF document management.

Handles listing and downloading PDFs from Azure Blob Storage container.
Generates SAS tokens for secure, time-limited access to documents.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from azure.storage.blob import (
    BlobServiceClient,
    ContainerClient,
    generate_blob_sas,
    BlobSasPermissions,
)

from backend.app.core.config import settings
from backend.app.core.logging import get_logger

logger = get_logger(__name__)

# SAS token expiry time (hours)
SAS_TOKEN_EXPIRY_HOURS = 24


@dataclass
class BlobDocument:
    """Represents a PDF document from blob storage."""
    
    filename: str
    content: bytes
    source_url: str
    size_bytes: int


class BlobService:
    """Service for interacting with Azure Blob Storage."""

    def __init__(self):
        """Initialize the blob service client."""
        self._blob_service_client: Optional[BlobServiceClient] = None
        self._container_client: Optional[ContainerClient] = None
        self._account_name: Optional[str] = None
        self._account_key: Optional[str] = None

    def _get_container_client(self) -> ContainerClient:
        """Get or create the container client."""
        if self._container_client is None:
            self._blob_service_client = BlobServiceClient.from_connection_string(
                settings.azure_storage_connection_string
            )
            self._container_client = self._blob_service_client.get_container_client(
                settings.azure_storage_container_name
            )
            # Extract account name and key for SAS generation
            self._parse_connection_string()
        return self._container_client

    def _parse_connection_string(self):
        """Parse connection string to extract account name and key."""
        conn_str = settings.azure_storage_connection_string
        parts = dict(part.split("=", 1) for part in conn_str.split(";") if "=" in part)
        self._account_name = parts.get("AccountName")
        self._account_key = parts.get("AccountKey")

    def generate_sas_url(
        self,
        blob_name: str,
        expiry_hours: int = SAS_TOKEN_EXPIRY_HOURS,
        inline: bool = True
    ) -> str:
        """
        Generate a SAS URL for secure, time-limited access to a blob.

        Args:
            blob_name: Name of the blob
            expiry_hours: Hours until the SAS token expires
            inline: If True, set content-disposition to inline for browser viewing

        Returns:
            Full URL with SAS token for accessing the blob
        """
        # Ensure we have the account credentials
        if not self._account_name or not self._account_key:
            self._get_container_client()

        if not self._account_name or not self._account_key:
            logger.warning("Could not extract account credentials, falling back to base URL")
            return settings.get_blob_url(blob_name)

        try:
            # Set content-disposition to inline so PDF opens in browser instead of downloading
            content_disposition = "inline" if inline else None

            sas_token = generate_blob_sas(
                account_name=self._account_name,
                container_name=settings.azure_storage_container_name,
                blob_name=blob_name,
                account_key=self._account_key,
                permission=BlobSasPermissions(read=True),
                expiry=datetime.now(timezone.utc) + timedelta(hours=expiry_hours),
                content_disposition=content_disposition,
                content_type="application/pdf"
            )

            # Construct the full URL with SAS token
            base_url = f"https://{self._account_name}.blob.core.windows.net"
            full_url = f"{base_url}/{settings.azure_storage_container_name}/{blob_name}?{sas_token}"

            return full_url

        except Exception as e:
            logger.error(f"Error generating SAS token for {blob_name}: {type(e).__name__}")
            # Fallback to base URL (won't work if public access is disabled)
            return settings.get_blob_url(blob_name)
    
    def list_pdf_blobs(self) -> List[str]:
        """
        List all PDF files in the configured container.
        
        Returns:
            List of PDF filenames
        """
        container = self._get_container_client()
        pdf_files = []
        
        try:
            blobs = container.list_blobs()
            for blob in blobs:
                if blob.name.lower().endswith('.pdf'):
                    pdf_files.append(blob.name)
            
            logger.info(f"Found {len(pdf_files)} PDF files in container")
            return pdf_files
            
        except Exception as e:
            logger.error(f"Error listing blobs: {type(e).__name__}")
            raise
    
    def download_pdf(self, filename: str) -> BlobDocument:
        """
        Download a PDF file from blob storage.

        Args:
            filename: Name of the PDF file to download

        Returns:
            BlobDocument containing the file content and metadata
        """
        container = self._get_container_client()

        try:
            blob_client = container.get_blob_client(filename)
            download_stream = blob_client.download_blob()
            content = download_stream.readall()

            # Generate SAS URL for secure access to the document
            source_url = self.generate_sas_url(filename)

            logger.info(f"Downloaded PDF: {filename} ({len(content)} bytes)")

            return BlobDocument(
                filename=filename,
                content=content,
                source_url=source_url,
                size_bytes=len(content)
            )

        except Exception as e:
            logger.error(f"Error downloading blob {filename}: {type(e).__name__}")
            raise
    
    def download_all_pdfs(self) -> List[BlobDocument]:
        """
        Download all PDF files from the container.
        
        Returns:
            List of BlobDocument objects
        """
        pdf_files = self.list_pdf_blobs()
        documents = []
        
        for filename in pdf_files:
            try:
                doc = self.download_pdf(filename)
                documents.append(doc)
            except Exception as e:
                logger.warning(f"Failed to download {filename}: {type(e).__name__}")
                continue
        
        logger.info(f"Successfully downloaded {len(documents)} of {len(pdf_files)} PDFs")
        return documents
