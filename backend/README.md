# Assistant API (FastAPI)

Async FastAPI service with optional JWT auth, structured audit events, and streaming chat completions via Ollama (swap for vLLM using `ASSISTANT_LLM_BACKEND`).

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp ../.env.example ../.env   # or export vars manually
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

OpenAPI: `http://localhost:8000/api/openapi.json`  
Docs (disable in prod via `ASSISTANT_DOCS_ENABLED=false`): `http://localhost:8000/docs`

## Configuration

See `app/config.py` — all settings use the `ASSISTANT_` prefix in the environment.
