# Implementation Plan — Enterprise Air-Gapped Coding Assistant

**Role:** Tech lead execution plan (tasks, order, ownership boundaries).  
**Does not replace:** Architecture / roadmap document — this is delivery-focused only.

---

# PHASE 1 — Repository Bootstrap

## Exact folders to create

```
/
├── backend/
│   ├── app/
│   │   ├── api/v1/
│   │   ├── core/
│   │   └── services/llm/
│   └── tests/
├── extension/
│   ├── src/
│   │   ├── api/
│   │   ├── chat/
│   │   ├── commands/
│   │   └── auth/
│   └── media/
├── infra/
│   ├── docker/
│   ├── helm/assistant-api/
│   └── compose/
├── contracts/              # OpenAPI exports (generated or hand-maintained)
├── docs/
└── .devcontainer/
```

## Exact files to create (minimum viable repo contract)

| Path | Purpose |
|------|---------|
| `README.md` | How to run locally, env vars, security notes |
| `.gitignore` | Python/Node/Docker/IDE artifacts |
| `.env.example` | Documented variables (no secrets) |
| `backend/pyproject.toml` | Locked-ish deps, tooling entry points |
| `backend/app/main.py` | App factory, middleware wiring |
| `backend/app/config.py` | `pydantic-settings` single source of truth |
| `extension/package.json` | VS Code extension manifest + scripts |
| `extension/tsconfig.json` | Strict TS for extension host |
| `infra/compose/docker-compose.yml` | Local API + Ollama profiles |
| `infra/docker/backend.Dockerfile` | Multi-stage API image |
| `.devcontainer/devcontainer.json` | Reproducible dev env |

## Dependencies to install

**Backend (pin versions in `pyproject.toml`):**

- `fastapi`, `uvicorn[standard]`
- `pydantic`, `pydantic-settings`
- `httpx` (async HTTP + streaming to Ollama/vLLM)
- `python-jose[cryptography]` (JWT validation)
- `structlog` (structured logs; optional but recommended)

**Extension:**

- `vscode` API types (`@types/vscode`)
- Build: `typescript`, `webpack` or `esbuild`
- Runtime: none beyond Node bundled with VS Code

## Docker setup

- **API image:** non-root user, multi-stage build, **no secrets baked in**, health/readiness endpoints.
- **Compose profiles:** `api`, `ollama` — Ollama optional on developer laptops with GPU.

## Environment variable strategy

- **12-factor:** `ASSISTANT_*` prefix for app settings (see `backend/app/config.py`).
- **Secrets:** never in compose `environment:` for prod — use K8s Secrets + CSI/external vault integration.
- **Hierarchy:** `.env` local only (gitignored); production via Helm `values` + Secret refs.

## Local development setup

1. Python venv from `backend/pyproject.toml`
2. `uvicorn app.main:app --reload` from `backend/`
3. Extension: `npm install` + `npm run watch` + F5 launch
4. Ollama: host-native or compose service pointing to `OLLAMA_BASE_URL`

## Devcontainer setup

- Base image with Python **and** Node LTS
- Post-create: install backend deps + extension deps
- Forward ports: `8000` (API), optional `11434` (Ollama if in-container)

## Terminal commands (bootstrap)

```bash
cd backend && python -m venv .venv && source .venv/bin/activate
pip install -U pip && pip install -e ".[dev]"
cd ../extension && npm install
```

## Package installations

See `backend/pyproject.toml` and `extension/package.json` in this repo.

## Initial FastAPI setup

Implemented under `backend/app/` — app factory pattern (`create_app()`), versioned routers under `api/v1/`.

## VS Code extension scaffold setup

Implemented under `extension/` — activation registers commands + chat panel.

## Docker compose setup

See `infra/compose/docker-compose.yml`.

---

# PHASE 2 — Backend Core

## Technical design breakdown

| Area | Decision | Why |
|------|-----------|-----|
| App shape | `create_app()` factory | Testability, multiple ASGI apps (unit vs integration) |
| Routers | `/api/v1/*` | Clear versioning; extension pins contract |
| Services | `services/llm/*` behind protocol | Swap Ollama ↔ vLLM without router edits |
| Middleware order | See below | Security + observability before business logic |
| Async | `async def` + `httpx.AsyncClient` | Streaming I/O without thread blocking |

### Middleware order (early implementation)

1. `TrustedHostMiddleware` (if enabled)
2. `CORSMiddleware` (locked origins in prod)
3. Request ID + trace context
4. JWT auth (optional via `ASSISTANT_AUTH_ENABLED`)
5. RBAC dependency per route (not global — explicit)

### RBAC implementation

- **Roles** in JWT claims (`realm_access.roles` or custom `roles: []`) — map to app permissions in `core/rbac.py`.
- **Enforcement:** FastAPI dependencies (`RequirePermission("chat:complete")`).

### Audit logging

- **Structured events** to stdout (Fluent Bit → SIEM); never log raw prompts by default — configurable.

### SSE streaming

- **Endpoint:** `POST /api/v1/chat/completions` with `stream: true` → `StreamingResponse`, `media_type="text/event-stream"`.
- **Protocol:** SSE `data: {json}\n\n` chunks; final `[DONE]` sentinel compatible with OpenAI-style clients.

### Ollama integration

- **HTTP:** `POST {OLLAMA_BASE_URL}/api/chat` with `stream: true`.
- **Parse:** NDJSON lines; map to unified `ChatStreamChunk` domain model.

### Request validation

- Pydantic models for request bodies; shared types in `app/schemas/`.

### Structured errors

- RFC7807-style JSON (`application/problem+json`) via exception handlers in `main.py`.

## File-by-file implementation order

1. `config.py` — settings & feature flags  
2. `core/errors.py`, `core/request_context.py`  
3. `schemas/chat.py` — request/response DTOs  
4. `services/llm/base.py` — protocol  
5. `services/llm/ollama.py` — adapter  
6. `services/llm/factory.py` — `LLMBackend` enum + selector  
7. `api/v1/chat.py` — SSE route  
8. `api/v1/health.py` — `/healthz`, `/readyz`  
9. `main.py` — wire routers + handlers  

## Interface contracts (summary)

- `LLMClient.stream_chat(messages, model, **kwargs) -> AsyncIterator[str]` — yields SSE-ready JSON fragments or normalized chunk dict (implementation choice: normalize in service, serialize in route).

## Code skeletons

Implemented in repository (`backend/app/`).

---

# PHASE 3 — VS CODE EXTENSION

## Extension architecture

- **Thin activation:** register commands, `AssistantApiClient`, `ChatPanelProvider`.
- **Separation:** UI (webview) never holds tokens — extension host performs `fetch` with auth headers.

## TypeScript module breakdown

| Module | Responsibility |
|--------|----------------|
| `extension.ts` | Lifecycle, command registration |
| `api/client.ts` | Streaming HTTP (SSE parse), timeouts, cancellation |
| `auth/tokenStore.ts` | Wrap `SecretStorage` |
| `chat/ChatPanelProvider.ts` | Webview lifecycle + message bridge |
| `commands/*.ts` | Explain/debug wrappers later |

## Message passing flow

1. Webview posts `{command:'send', text}` → extension  
2. Extension calls `client.streamChat()` → reads SSE stream  
3. Extension posts `{type:'chunk', delta}` → webview until `done`/`error`

## API client structure

- Base URL from `vscode.workspace.getConfiguration('assistant')`
- Headers: `Authorization`, `X-Request-Id`, `X-Assistant-Feature`

## VS Code APIs to use

- `vscode.window.createWebviewPanel`
- `vscode.authentication` (future SSO) / `SecretStorage` (PAT)
- `vscode.workspace.getConfiguration`
- `vscode.commands.registerCommand`

---

# PHASE 4 — ENTERPRISE SECURITY

## Implementation plan

| Control | Implementation |
|---------|----------------|
| JWT | `python-jose` decode + issuer/audience checks; JWKS URL optional |
| OIDC | Same JWT validation; obtain tokens via corporate IdP (extension flow out-of-band in MVP: PAT in Secret Storage) |
| mTLS | Terminate at ingress **or** API verifies client cert if platform injects headers |
| RBAC | Dependencies + centralized permission map |
| Audit | `audit.emit(event)` with stable schema |
| Redaction | Regex patterns on outbound logs & optional pre-storage |
| Tracing | `X-Request-Id` + OpenTelemetry hooks (stub now, enable later) |

### Middleware order (final production target)

1. Security headers (HSTS etc. at ingress — app adds minimal set)
2. Request ID
3. AuthN (JWT)
4. Rate limit (Redis — phase later)
5. Route handlers with AuthZ deps

### Production hardening checklist

- [ ] Non-root container  
- [ ] Read-only root filesystem  
- [ ] `ALLOWED_HOSTS` / CORS allowlist  
- [ ] Max body size limits  
- [ ] TLS only externally  
- [ ] Secrets from CSI/Vault  
- [ ] SBOM + signed images  
- [ ] NetworkPolicies default deny  

---

# PHASE 5 — KUBERNETES + DEPLOYMENT

## Helm chart structure

See `infra/helm/assistant-api/` — Deployment, Service, Ingress, ConfigMap, optional NetworkPolicy, ServiceMonitor stub.

## Manifests

- **Deployment:** probes use `/api/v1/healthz` (liveness) and `/api/v1/readyz` (readiness).
- **Ingress:** TLS secret name parameterized.

## GPU scheduling

- Inference chart (separate) adds `resources.limits.nvidia.com/gpu`, node selectors/taints.

## Autoscaling

- API: HPA on CPU/memory + custom metric later  
- GPU: avoid naive HPA — use queue depth / fixed pool  

## ConfigMaps vs Secrets

- ConfigMap: non-sensitive feature flags, model allowlist  
- Secrets: JWT signing keys, DB URLs, API keys  

## NetworkPolicies

- API namespace: allow ingress-controller → API only  
- Inference namespace: allow API → inference only; deny egress  

## Observability stack

- Prometheus scrape annotations (optional)  
- Structured logs to cluster collector  

---

# PHASE 6 — OLLAMA → VLLM MIGRATION

## Adapter pattern

- `LLMBackend` enum + `create_llm_client(settings)` returns unified protocol implementation.

## Feature flags

- `ASSISTANT_LLM_BACKEND=ollama|vllm_openai`

## Rollout

1. Deploy vLLM service internal-only  
2. Canary percentage via gateway or weighted DNS (platform choice)  
3. Compare latency/token throughput dashboards  

## Testing / benchmarking

- Contract tests: same golden prompts, compare outputs shape (not necessarily byte-identical)  
- Load: **k6** or **Locust** against `/chat/completions` streaming  

---

# PHASE 7 — CI/CD FOR AIR-GAPPED ENVIRONMENTS

## Pipeline stages (GitLab CI / Jenkins analogous)

1. Lint + unit tests  
2. SAST (SonarQube / Semgrep)  
3. Build images → push to staging registry  
4. Sign images (**Cosign**)  
5. Generate SBOM (**Syft**)  
6. Promote digest via controlled promotion job (offline bundle export optional)  

## Offline artifact promotion

- Export `docker save` tar + Helm chart `.tgz` + provenance manifest via approved transfer.

## Private registry

- Harbor / Artifactory — **immutable tags**, retention policies.

---

# PHASE 8 — TESTING STRATEGY

| Layer | Tooling |
|-------|---------|
| Unit | `pytest` for services & RBAC mapping |
| Integration | `httpx.AsyncClient` against TestClient / ephemeral Postgres later |
| Load | k6 streaming scenarios |
| Model eval | Offline golden set in `evals/` (no CI dependency on GPU if optional) |
| Security | OWASP ZAP baseline in staging, container scans |
| Extension | `@vscode/test-electron` |
| K8s | `helm unittest`, kubeconform for manifests |

---

# PHASE 9 — MVP EXECUTION PLAN

## Week-by-week (indicative)

| Week | Deliverable | Owner suggestion |
|------|-------------|------------------|
| 1 | Repo bootstrap + compose + health endpoints | Platform / backend |
| 2 | Ollama streaming + extension chat reads stream | Backend + frontend |
| 3 | JWT + RBAC + audit MVP | Security-focused backend |
| 4 | Helm + ingress + NetworkPolicy baseline | Platform |
| 5 | Load test + hardening fixes | Backend + platform |

## Critical path

Extension streaming ↔ API SSE ↔ Ollama stream parsing ↔ GPU availability.

## Risks

- Corporate TLS interception breaking httpx — trust store mounting  
- Prompt retention policy conflicts — legal/compliance early  

## Blockers

- Private registry access  
- IdP integration timeline  
- GPU node provisioning  

---

# PHASE 10 — CODE GENERATION

**Starter implementation lives in this repository:**

| Artifact | Path |
|----------|------|
| FastAPI app | `backend/app/main.py`, `backend/app/api/v1/*` |
| Ollama adapter | `backend/app/services/llm/ollama.py` |
| SSE endpoint | `backend/app/api/v1/chat.py` |
| JWT middleware | `backend/app/core/security.py`, `backend/app/api/deps.py` |
| VS Code client | `extension/src/api/client.ts` |
| Streaming chat UI | `extension/src/chat/*`, `extension/media/*` |
| Docker | `infra/docker/backend.Dockerfile`, `infra/compose/docker-compose.yml` |
| Helm starter | `infra/helm/assistant-api/*` |

**Architectural decisions** are documented inline in file docstrings / comments.
