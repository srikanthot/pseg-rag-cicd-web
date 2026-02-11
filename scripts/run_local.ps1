# Local development script for RAG Chatbot (Windows PowerShell)
# Starts both backend and UI servers

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir

Set-Location $ProjectRoot

# Check for .env file
if (-not (Test-Path ".env")) {
    Write-Host "Error: .env file not found!" -ForegroundColor Red
    Write-Host "Please copy .env.example to .env and fill in your Azure credentials."
    exit 1
}

# Check for virtual environment
if (-not (Test-Path ".venv")) {
    Write-Host "Creating virtual environment..."
    python -m venv .venv
}

# Activate virtual environment
& .\.venv\Scripts\Activate.ps1

# Install dependencies
Write-Host "Installing dependencies..."
pip install -r requirements.txt --quiet

# Set PYTHONPATH
$env:PYTHONPATH = $ProjectRoot

Write-Host ""
Write-Host "Starting servers..." -ForegroundColor Green
Write-Host ""

# Start backend server in new window
$backendJob = Start-Job -ScriptBlock {
    param($root)
    Set-Location $root
    & .\.venv\Scripts\Activate.ps1
    $env:PYTHONPATH = $root
    uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
} -ArgumentList $ProjectRoot

# Wait for backend to start
Start-Sleep -Seconds 3

# Start Streamlit UI in new window
$uiJob = Start-Job -ScriptBlock {
    param($root)
    Set-Location "$root\ui"
    & "$root\.venv\Scripts\Activate.ps1"
    streamlit run streamlit_app.py --server.port 8501 --server.address 0.0.0.0
} -ArgumentList $ProjectRoot

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "RAG Chatbot is running!" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Backend API:  http://localhost:8000" -ForegroundColor Yellow
Write-Host "  API Docs:     http://localhost:8000/docs" -ForegroundColor Yellow
Write-Host "  Streamlit UI: http://localhost:8501" -ForegroundColor Yellow
Write-Host ""
Write-Host "Press Ctrl+C to stop all servers."
Write-Host ""

try {
    # Keep script running and show job output
    while ($true) {
        Receive-Job -Job $backendJob -ErrorAction SilentlyContinue
        Receive-Job -Job $uiJob -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 1
    }
}
finally {
    # Cleanup
    Write-Host ""
    Write-Host "Shutting down servers..."
    Stop-Job -Job $backendJob -ErrorAction SilentlyContinue
    Stop-Job -Job $uiJob -ErrorAction SilentlyContinue
    Remove-Job -Job $backendJob -Force -ErrorAction SilentlyContinue
    Remove-Job -Job $uiJob -Force -ErrorAction SilentlyContinue
}
