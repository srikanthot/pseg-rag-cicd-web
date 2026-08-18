# RAG CI/CD Template — GitHub Actions + Docker

> A production-shaped RAG chatbot with **CI/CD baked in** — GitHub Actions, Docker, a Streamlit UI, and a FastAPI backend. Fork it as the starting point for a deployable RAG service.

![status](https://img.shields.io/badge/status-reference%20architecture-brightgreen) ![focus](https://img.shields.io/badge/focus-MLOps%20%2F%20CI--CD-2088FF) ![python](https://img.shields.io/badge/python-3.11-blue) ![docker](https://img.shields.io/badge/docker-ready-2496ED) ![license](https://img.shields.io/badge/license-MIT-lightgrey)


---

## Why this exists

Most RAG repos stop at "runs on my machine." This one ships the boring, essential parts: containerized build, GitHub Actions pipeline, environment config, health checks, and a deploy path to Azure App Service.

## Architecture

```mermaid
flowchart LR
    DEV[Push / PR] --> GHA[GitHub Actions<br/>lint · test · build]
    GHA --> IMG[Docker image]
    IMG --> APP[Azure App Service]
    UI[Streamlit UI] --> API[FastAPI backend]
    API --> SEARCH[(Azure AI Search)]
    API --> AOAI[Azure OpenAI]
```

## Features
- **GitHub Actions** CI/CD (build, deploy) with secrets via GitHub Secrets.
- **Docker** container + compose for local.
- **RAG core** — Blob ingestion, hybrid search, strict grounding, SAS-secured citations.
- Health endpoints + operational docs.

## Quickstart
```bash
cp .env.example .env
docker compose up            # UI + API locally
```

## Roadmap
- **Eval quality gate** — run the [rag-evaluation-harness-python](https://github.com/srikanthot/rag-evaluation-harness-python) suite in CI and block merge on regression.
- Bicep/Terraform IaC; a parallel AWS deploy job.

---
