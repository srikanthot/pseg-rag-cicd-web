#!/bin/bash
# Local development script for RAG Chatbot
# Starts both backend and UI servers

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

# Check for .env file
if [ ! -f ".env" ]; then
    echo "Error: .env file not found!"
    echo "Please copy .env.example to .env and fill in your Azure credentials."
    exit 1
fi

# Check for virtual environment
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
source .venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt --quiet

# Export PYTHONPATH
export PYTHONPATH="$PROJECT_ROOT"

# Function to cleanup background processes
cleanup() {
    echo ""
    echo "Shutting down servers..."
    kill $BACKEND_PID 2>/dev/null || true
    kill $UI_PID 2>/dev/null || true
    exit 0
}

trap cleanup SIGINT SIGTERM

# Start backend server
echo ""
echo "Starting backend server on http://localhost:8000..."
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

# Wait for backend to start
sleep 3

# Start Streamlit UI
echo ""
echo "Starting Streamlit UI on http://localhost:8501..."
cd ui
streamlit run streamlit_app.py --server.port 8501 --server.address 0.0.0.0 &
UI_PID=$!
cd ..

echo ""
echo "=========================================="
echo "RAG Chatbot is running!"
echo "=========================================="
echo ""
echo "  Backend API:  http://localhost:8000"
echo "  API Docs:     http://localhost:8000/docs"
echo "  Streamlit UI: http://localhost:8501"
echo ""
echo "Press Ctrl+C to stop all servers."
echo ""

# Wait for processes
wait
