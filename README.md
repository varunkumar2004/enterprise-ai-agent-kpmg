# Enterprise Air-Gapped Coding Assistant — Starter Repo

This repository contains an implementation-aligned scaffold:

- `backend/` — FastAPI control plane (JWT-ready, RBAC, SSE chat completions, Ollama + vLLM adapters).
- `extension/` — VS Code extension host client + webview chat streaming UI.
- `infra/` — Docker Compose, container image, Helm starter chart.

Operational guidance lives in `docs/IMPLEMENTATION_PLAN.md`.

## Local quick start

```bash
cd backend && python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

```bash
cd extension && npm install && npm run compile
```

Press **F5** in VS Code (Extension Development Host) after opening the `extension/` folder.

## Docker Compose

```bash
docker compose -f infra/compose/docker-compose.yml up --build
```

## Configuration

Copy `.env.example` to `.env` at repo root for tooling that reads env files, **or** export variables manually for `uvicorn`.
