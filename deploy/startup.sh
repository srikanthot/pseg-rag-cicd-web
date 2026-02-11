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

set -e

echo "=========================================="
echo " RAG Chatbot - Azure Web App Startup"
echo "=========================================="

# ── 1. Set internal backend port (not exposed to internet) ──
export BACKEND_PORT=8080
export BACKEND_HOST=0.0.0.0
export BACKEND_URL=http://localhost:8080

# ── 2. Navigate to app root ──
cd /home/site/wwwroot

# ── 3. Start FastAPI backend in the background ──
echo "[startup] Starting FastAPI backend on port 8080..."
gunicorn \
    -k uvicorn.workers.UvicornWorker \
    backend.app.main:app \
    --bind 0.0.0.0:8080 \
    --workers 2 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - &

BACKEND_PID=$!
echo "[startup] FastAPI backend started (PID: $BACKEND_PID)"

# ── 4. Wait for backend to be ready ──
echo "[startup] Waiting for backend to be ready..."
for i in $(seq 1 30); do
    if curl -sf http://localhost:8080/health > /dev/null 2>&1; then
        echo "[startup] Backend is ready!"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "[startup] WARNING: Backend not responding after 30s, starting UI anyway..."
    fi
    sleep 1
done

# ── 5. Start Streamlit frontend on port 8000 (FOREGROUND) ──
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
