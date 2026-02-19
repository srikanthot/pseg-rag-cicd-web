#!/bin/bash
# ============================================================
# Azure Web App Startup Script
# Runs BOTH FastAPI backend + Streamlit frontend on one App Service
#
# Architecture on a single Azure Web App:
#   ┌──────────────────────────────────────────────────────┐
#   │  Internet  ──►  port 8000 (WEBSITES_PORT)            │
#   │                     │                                 │
#   │              Streamlit (foreground)                   │
#   │                     │  http://localhost:8080          │
#   │              FastAPI / gunicorn (background)          │
#   │                     │                                 │
#   │              Azure OpenAI / Search / Blob             │
#   └──────────────────────────────────────────────────────┘
#
# FastAPI is INTERNAL only (port 8080, never exposed to internet).
# Streamlit is PUBLIC (port 8000, mapped via WEBSITES_PORT).
# ============================================================

LOG_DIR="/home/LogFiles"
BACKEND_LOG="$LOG_DIR/backend.log"
APP_ROOT="/home/site/wwwroot"

echo "=========================================="
echo " RAG Chatbot – Azure Web App Startup"
echo " $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
echo "=========================================="

# ── 1. Environment ──────────────────────────────────────────
export BACKEND_PORT=8080
export BACKEND_HOST=0.0.0.0
export BACKEND_URL=http://localhost:8080
export PYTHONPATH=$APP_ROOT
export PYTHONUNBUFFERED=1

echo "[startup] PYTHONPATH   = $PYTHONPATH"
echo "[startup] BACKEND_URL  = $BACKEND_URL"
echo "[startup] LOG_LEVEL    = ${LOG_LEVEL:-INFO}"

# ── 2. Navigate to app root ──────────────────────────────────
cd "$APP_ROOT" || { echo "[startup] ERROR: $APP_ROOT not found!"; exit 1; }

# ── 3. Validate critical files ───────────────────────────────
echo "[startup] Validating app structure..."
for f in backend/app/main.py ui/streamlit_app.py requirements.txt; do
  if [ ! -f "$f" ]; then
    echo "[startup] ERROR: Missing required file: $f"
    exit 1
  fi
done
echo "[startup] App structure OK."

# ── 4. Dependencies (handled by Oryx during deployment) ──────
#    Oryx builds a virtual environment at /antenv and installs
#    all packages from requirements.txt before this script runs.
#    Azure activates /antenv automatically before running the
#    startup command, so packages are already on the PATH.
echo "[startup] Python: $(python --version 2>&1)"
echo "[startup] Gunicorn: $(python -m gunicorn --version 2>&1)"

# ── 5. Start FastAPI backend (background, port 8080) ─────────
#    'python -m gunicorn' avoids PATH issues on Azure.
echo "[startup] Starting FastAPI backend on port 8080..."
mkdir -p "$LOG_DIR"

python -m gunicorn \
    -k uvicorn.workers.UvicornWorker \
    backend.app.main:app \
    --bind 0.0.0.0:$BACKEND_PORT \
    --workers 2 \
    --timeout 120 \
    --keep-alive 5 \
    --access-logfile - \
    --error-logfile - \
    > "$BACKEND_LOG" 2>&1 &

BACKEND_PID=$!
echo "[startup] FastAPI started (PID: $BACKEND_PID), log → $BACKEND_LOG"

# ── 6. Wait for backend to be ready ─────────────────────────
echo "[startup] Waiting for FastAPI to be ready (up to 60s)..."
READY=false
for i in $(seq 1 60); do
    if curl -sf "http://localhost:$BACKEND_PORT/health" > /dev/null 2>&1; then
        echo "[startup] FastAPI is ready after ${i}s."
        READY=true
        break
    fi
    # Show progress every 10 seconds
    if [ $((i % 10)) -eq 0 ]; then
        echo "[startup] Still waiting... ${i}s elapsed"
    fi
    sleep 1
done

if [ "$READY" = "false" ]; then
    echo "[startup] WARNING: FastAPI did not respond in 60s."
    echo "[startup] Backend log (last 40 lines):"
    tail -40 "$BACKEND_LOG" 2>/dev/null || echo "[startup] No backend log yet."
    # Check if process is still alive before continuing
    if ! kill -0 $BACKEND_PID 2>/dev/null; then
        echo "[startup] CRITICAL: FastAPI process has crashed."
        echo "[startup] Streamlit will start anyway but API calls will fail."
    fi
fi

# ── 7. Start Streamlit frontend (foreground, port 8000) ──────
#    exec replaces this shell so Azure can track the process.
#    Azure Web App exposes WEBSITES_PORT=8000 to the internet.
echo "[startup] Starting Streamlit on port 8000 (public)..."
cd "$APP_ROOT/ui" || { echo "[startup] ERROR: ui/ directory not found"; exit 1; }

exec python -m streamlit run streamlit_app.py \
    --server.port=8000 \
    --server.address=0.0.0.0 \
    --server.headless=true \
    --server.enableCORS=false \
    --server.enableXsrfProtection=false \
    --server.enableWebsocketCompression=false \
    --browser.gatherUsageStats=false
