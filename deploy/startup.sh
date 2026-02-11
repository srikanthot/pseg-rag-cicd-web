#!/bin/bash
# ============================================================
# Azure Web App Startup Script
# Runs BOTH FastAPI backend + Streamlit frontend on one App Service
#
# How it works:
#   - FastAPI (gunicorn) runs in the BACKGROUND on port 8080
#   - Streamlit runs in the FOREGROUND on port 8000
#   - Azure Web App exposes port 8000 to the internet
#   - Streamlit talks to FastAPI via http://localhost:8080
# ============================================================

# Do NOT use set -e — we want both processes to start even if health check fails

LOG_DIR="/home/LogFiles"
BACKEND_LOG="$LOG_DIR/backend.log"

echo "=========================================="
echo " RAG Chatbot - Azure Web App Startup"
echo "=========================================="

# ── 1. Set internal backend port (not exposed to internet) ──
export BACKEND_PORT=8080
export BACKEND_HOST=0.0.0.0
export BACKEND_URL=http://localhost:8080
export PYTHONPATH=/home/site/wwwroot

# ── 2. Navigate to app root ──
cd /home/site/wwwroot

# ── 3. Log environment for debugging (no secrets) ──
echo "[startup] PYTHONPATH=$PYTHONPATH"
echo "[startup] BACKEND_URL=$BACKEND_URL"
echo "[startup] Checking if backend module exists..."
ls -la backend/app/main.py 2>&1 || echo "[startup] WARNING: backend/app/main.py not found!"

# ── 4. Install dependencies if not already installed ──
echo "[startup] Ensuring dependencies are installed..."
pip install -r requirements.txt --quiet 2>&1 | tail -5

# ── 5. Start FastAPI backend in the background ──
echo "[startup] Starting FastAPI backend on port 8080..."
gunicorn \
    -k uvicorn.workers.UvicornWorker \
    backend.app.main:app \
    --bind 0.0.0.0:8080 \
    --workers 2 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    > "$BACKEND_LOG" 2>&1 &

BACKEND_PID=$!
echo "[startup] FastAPI backend started (PID: $BACKEND_PID)"

# ── 6. Wait for backend to be ready ──
echo "[startup] Waiting for backend to be ready..."
for i in $(seq 1 45); do
    if curl -sf http://localhost:8080/health > /dev/null 2>&1; then
        echo "[startup] Backend is ready after ${i}s!"
        break
    fi
    if [ $i -eq 45 ]; then
        echo "[startup] WARNING: Backend not responding after 45s"
        echo "[startup] Backend log (last 30 lines):"
        tail -30 "$BACKEND_LOG" 2>/dev/null || echo "[startup] No backend log available"
        # Check if process is still running
        if kill -0 $BACKEND_PID 2>/dev/null; then
            echo "[startup] Backend process is still running, may need more time..."
        else
            echo "[startup] ERROR: Backend process has crashed! Check $BACKEND_LOG"
        fi
    fi
    sleep 1
done

# ── 7. Start Streamlit frontend on port 8000 (FOREGROUND) ──
#    Azure Web App expects the main process on port 8000
echo "[startup] Starting Streamlit frontend on port 8000..."
cd /home/site/wwwroot/ui
exec streamlit run streamlit_app.py \
    --server.port=8000 \
    --server.address=0.0.0.0 \
    --server.headless=true \
    --server.enableCORS=false \
    --server.enableXsrfProtection=false \
    --browser.gatherUsageStats=false
