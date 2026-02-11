# PSEG RAG Chatbot - Demo Documentation

## Project Overview

This is an **Enterprise RAG (Retrieval-Augmented Generation) Chatbot** that allows users to ask questions about PSEG technical manuals and receive accurate, citation-backed answers from PDF documents stored in Azure Blob Storage.

### Key Features
- **AI-Powered Q&A**: Uses Azure OpenAI GPT-4o-mini for intelligent responses
- **Citation-Backed Answers**: Every answer includes clickable links to source PDFs with page numbers
- **Secure Document Access**: Uses SAS tokens for time-limited, secure PDF access
- **Enterprise UI**: Professional PSEG-branded Streamlit interface
- **Hybrid Search**: Combines vector (semantic) + keyword search for better results

---

## Folder Structure

```
Rag_new-main/
│
├── .env                    # ⚠️ CONFIGURATION FILE (API Keys go here)
├── .env.example            # Template for .env file
├── requirements.txt        # Python dependencies
├── README.md               # Basic readme
│
├── backend/                # 🔧 BACKEND API (FastAPI)
│   └── app/
│       ├── main.py         # ⭐ MAIN BACKEND ENTRY POINT
│       ├── api/
│       │   ├── routes_chat.py      # /api/chat endpoint
│       │   ├── routes_health.py    # /health endpoint
│       │   └── routes_ingest.py    # /api/ingest endpoint
│       ├── core/
│       │   ├── config.py           # ⭐ Loads settings from .env
│       │   └── logging.py          # Logging configuration
│       ├── models/
│       │   └── schemas.py          # Data models (ChatRequest, ChatResponse, etc.)
│       ├── services/
│       │   ├── rag_service.py      # ⭐ MAIN RAG LOGIC (orchestrates everything)
│       │   ├── search_service.py   # Azure AI Search operations
│       │   ├── embed_service.py    # Azure OpenAI embeddings
│       │   ├── blob_service.py     # Azure Blob Storage + SAS URLs
│       │   ├── pdf_service.py      # PDF text extraction
│       │   └── chunk_service.py    # Text chunking logic
│       └── utils/
│           ├── thresholds.py       # Score threshold gating
│           └── text.py             # Text utilities
│
├── ui/                     # 🎨 FRONTEND UI (Streamlit)
│   ├── streamlit_app.py    # ⭐ MAIN UI ENTRY POINT
│   ├── components/
│   │   ├── chat_panel.py       # Chat history & messages
│   │   ├── sidebar_controls.py # Sidebar with settings
│   │   └── citations_panel.py  # Citation display
│   └── assets/             # Static assets (logo, etc.)
│
├── scripts/                # Utility scripts
│   └── create_search_index.py  # Create Azure Search index
│
├── docker/                 # Docker configuration
├── docs/                   # Documentation
└── infra/                  # Infrastructure as Code
```

---

## Key Files Explained

### 1. `.env` - Configuration File (⚠️ MOST IMPORTANT)

**Location**: Project root (`Rag_new-main/.env`)

This file contains ALL API keys and configuration. Your lead must create this file with their own Azure credentials.

```env
# Azure OpenAI Configuration
AZURE_OPENAI_ENDPOINT=https://your-openai-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key-here
AZURE_OPENAI_API_VERSION=2024-12-01-preview
AZURE_OPENAI_CHAT_DEPLOYMENT=gpt-4o-mini
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-3-small

# Azure AI Search Configuration
AZURE_SEARCH_ENDPOINT=https://your-search-service.search.windows.net
AZURE_SEARCH_API_KEY=your-search-api-key
AZURE_SEARCH_INDEX_NAME=pseg-pdfs-index

# Azure Blob Storage Configuration
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=...
AZURE_STORAGE_CONTAINER_NAME=pdfs
BLOB_BASE_URL=https://your-storage.blob.core.windows.net/pdfs

# RAG Tuning Parameters
TOP_K=5
SCORE_THRESHOLD=0.01
STRICT_GROUNDING=true
```

### 2. `backend/app/main.py` - Backend Entry Point

Starts the FastAPI server with these endpoints:
- `POST /api/chat` - Main chat endpoint (question → answer + citations)
- `POST /api/ingest` - Ingest PDFs from blob storage into search index
- `GET /health` - Health check endpoint

### 3. `backend/app/services/rag_service.py` - Core RAG Logic

**This is the brain of the application.** It:
1. Takes user question
2. Creates embedding using Azure OpenAI
3. Searches Azure AI Search for relevant chunks
4. Passes chunks to GPT-4o-mini for answer generation
5. Builds citations with secure SAS URLs
6. Returns answer + citations

### 4. `backend/app/services/blob_service.py` - PDF Storage

Handles:
- Listing PDFs in Azure Blob Storage
- Downloading PDFs for processing
- Generating SAS URLs (secure, time-limited links) for citations

### 5. `backend/app/services/search_service.py` - Vector Search

Handles:
- Creating/managing Azure AI Search index
- Hybrid search (vector + keyword)
- Indexing document chunks

### 6. `ui/streamlit_app.py` - Main UI

The Streamlit frontend that:
- Displays PSEG branded header
- Shows chat interface
- Renders citations with "Open" buttons
- Provides sidebar controls

### 7. `ui/components/sidebar_controls.py` - Sidebar

Contains:
- Search settings (number of sources, confidence threshold)
- Document ingestion button
- System status indicator
- Clear chat button

---

## Azure Resources Required

Your lead needs to create these Azure resources:

| Resource | Purpose | Key Settings |
|----------|---------|--------------|
| **Azure OpenAI** | LLM + Embeddings | Deploy `gpt-4o-mini` and `text-embedding-3-small` models |
| **Azure AI Search** | Vector database | Basic tier or higher, enable semantic search |
| **Azure Blob Storage** | PDF storage | Create container named `pdfs`, upload PDFs there |

---

## How the RAG Flow Works

```
1. User asks: "What is the flood hazard procedure?"
                    │
                    ▼
2. UI sends question to Backend API
                    │
                    ▼
3. Backend creates embedding of question
   (Azure OpenAI text-embedding-3-small)
                    │
                    ▼
4. Hybrid search in Azure AI Search
   - Vector similarity search
   - Keyword matching
   - Returns top 5 relevant chunks
                    │
                    ▼
5. Quality check (score threshold)
   - If scores too low → "Out of context" response
   - If scores OK → Continue
                    │
                    ▼
6. Send chunks + question to GPT-4o-mini
   - System prompt enforces citation rules
   - Model generates answer from sources only
                    │
                    ▼
7. Build citations with SAS URLs
   - Generate secure, time-limited PDF links
   - Add page number anchors (#page=X)
                    │
                    ▼
8. Return response to UI
   - Answer text
   - Citations with clickable "Open" buttons
   - Out-of-context flag if applicable
```

---

## Commands to Run the Application

### Prerequisites
- Python 3.10+ installed
- Azure resources created (see above)
- `.env` file configured with API keys

### Step 1: Clone Repository
```bash
git clone https://github.com/your-username/pseg-rag-chatbot.git
cd pseg-rag-chatbot
```

### Step 2: Create Virtual Environment
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Mac/Linux
python3 -m venv .venv
source .venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment
```bash
# Copy the example file
copy .env.example .env    # Windows
cp .env.example .env      # Mac/Linux

# Edit .env with your Azure credentials
notepad .env              # Windows
nano .env                 # Mac/Linux
```

### Step 5: Upload PDFs to Azure Blob Storage
Upload your PDF files to the Azure Blob Storage container (named `pdfs`).

### Step 6: Start Backend Server
```bash
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Step 7: Start Frontend UI (New Terminal)
```bash
cd ui
streamlit run streamlit_app.py --server.port 8501
```

### Step 8: Ingest Documents
1. Open browser: http://localhost:8501
2. Click "Ingest Documents" in sidebar
3. Wait for PDFs to be processed and indexed

### Step 9: Start Chatting!
Ask questions about your technical manuals.

---

## Quick Start (All Commands)

```bash
# Clone and setup
git clone https://github.com/your-username/pseg-rag-chatbot.git
cd pseg-rag-chatbot
python -m venv .venv
.venv\Scripts\activate              # Windows
pip install -r requirements.txt

# Configure (edit .env with your keys)
copy .env.example .env
notepad .env

# Start backend (Terminal 1)
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload

# Start frontend (Terminal 2)
cd ui
streamlit run streamlit_app.py --server.port 8501

# Open browser
# Backend: http://localhost:8000/docs (API documentation)
# Frontend: http://localhost:8501 (Chat UI)
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Cannot connect to backend" | Make sure backend is running on port 8000 |
| "API Error 401" | Check Azure API keys in .env file |
| "No results found" | Click "Ingest Documents" to index PDFs |
| "Score threshold blocking results" | Lower SCORE_THRESHOLD in .env (try 0.01) |
| "PDF link not working" | SAS token expired - re-query to get fresh URL |

---

## Demo Script

1. **Show Architecture**: Explain the 3 Azure services and how they connect
2. **Show .env file**: Explain where API keys are configured
3. **Start the app**: Run both backend and frontend
4. **Ingest documents**: Show the ingestion process
5. **Ask a relevant question**: Show answer with citations
6. **Click citation**: Show PDF opens to correct page
7. **Ask irrelevant question**: Show "out of context" handling
8. **Show sidebar**: Explain settings and their purpose

---

## Contact

For questions about this implementation, contact the development team.
