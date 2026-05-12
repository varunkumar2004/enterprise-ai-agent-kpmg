# Project status — task tracker

**Purpose:** Single place for **full-scope tasks**, **what’s done**, and **what’s left**.  
**Legend:** **Done** = shipped in repo · **Partial** = scaffold/stub exists · **Todo** = not started.

---

## How to use this file

- Update row status when a task merges (Done / Partial / Todo).
- Link PRs or tickets in your tracker beside tasks when applicable.
- “Partial” means engineering can continue without rework, but product/security acceptance is not complete.

---

## 1. Repository & developer experience

| # | Task | Status | Notes |
|---|------|--------|--------|
| 1.1 | Monorepo layout (`backend/`, `extension/`, `infra/`, `docs/`) | Done | |
| 1.2 | Root `README.md` (run instructions, env overview) | Done | |
| 1.3 | `.gitignore` (venv, secrets, `node_modules`, artifacts) | Done | |
| 1.4 | `.env.example` documenting `ASSISTANT_*` variables | Done | |
| 1.5 | Backend packaging (`pyproject.toml`, editable install) | Done | |
| 1.6 | Extension packaging (`package.json`, webpack build) | Done | |
| 1.7 | Dev Container (Python + Node) | Partial | `.devcontainer/devcontainer.json` present; validate post-create on CI image |
| 1.8 | VS Code workspace configs (`launch.json` for API + extension) | Done | `.vscode/launch.json` |
| 1.9 | Contracts folder for OpenAPI snapshots | Partial | `contracts/README.md` placeholder only |
| 1.10 | Makefile/Taskfile for common commands | Todo | Optional polish |

---

## 2. Backend — core API

| # | Task | Status | Notes |
|---|------|--------|--------|
| 2.1 | FastAPI app factory + lifespan | Done | `backend/app/main.py` |
| 2.2 | Shared async HTTP client (pooling / timeouts) | Done | Lifespan `httpx.AsyncClient` |
| 2.3 | Versioned router `/api/v1` | Done | |
| 2.4 | Health: `/healthz` | Done | |
| 2.5 | Readiness: `/readyz` | Partial | Returns static OK; add DB/Redis/inference checks when those exist |
| 2.6 | OpenAPI + `/docs` toggle via config | Partial | `ASSISTANT_DOCS_ENABLED`; disable in prod |
| 2.7 | Global exception handling → `problem+json` | Done | `AssistantHTTPException` |
| 2.8 | Request size limits | Done | `MaxBodySizeMiddleware` + setting |
| 2.9 | Trusted hosts / CORS (config-driven) | Partial | Wired; production values TBD |
| 2.10 | Request ID + `x-request-id` | Done | |
| 2.11 | Structured logging (JSON-friendly) | Partial | `structlog` JSON; ship-side aggregation TBD |

---

## 3. Backend — LLM integration

| # | Task | Status | Notes |
|---|------|--------|--------|
| 3.1 | LLM protocol + normalized stream deltas | Done | `services/llm/base.py` |
| 3.2 | Ollama adapter (`/api/chat` streaming) | Done | `services/llm/ollama.py` |
| 3.3 | vLLM OpenAI-compatible adapter | Partial | `services/llm/vllm_openai.py`; needs staging validation vs real vLLM |
| 3.4 | Backend selector `ASSISTANT_LLM_BACKEND` | Done | `services/llm/factory.py` |
| 3.5 | Chat completions (non-stream JSON) | Done | `POST /api/v1/chat/completions` |
| 3.6 | Chat completions (SSE / OpenAI-style chunks) | Done | Same route |
| 3.7 | Model allowlist / policy per tenant | Todo | Future RBAC + config |
| 3.8 | Token accounting / billing hooks | Todo | |
| 3.9 | Prompt templates versioning (Jinja/Mustache in repo) | Todo | |
| 3.10 | Offline eval harness (`evals/` golden tasks) | Todo | |

---

## 4. Backend — security & compliance

| # | Task | Status | Notes |
|---|------|--------|--------|
| 4.1 | JWT validation (HS256 + aud/iss) | Partial | `core/security.py`; add JWKS for prod |
| 4.2 | OIDC token acquisition (extension) | Todo | Use `vscode.authentication` or device code |
| 4.3 | mTLS (ingress or app-level client cert) | Todo | |
| 4.4 | RBAC (roles → permissions) | Partial | `core/rbac.py`; expand roles/claims |
| 4.5 | Enforce auth on all sensitive routes | Partial | Chat uses RBAC; health public by design |
| 4.6 | Audit events (who / what / outcome / request ID) | Partial | `core/audit.py` + hashes; retention policy TBD |
| 4.7 | Secret redaction (logs / outbound) | Partial | `core/redaction.py` starter patterns |
| 4.8 | Distributed rate limiting (Redis) | Todo | |
| 4.9 | OPA / external policy engine | Todo | Optional for complex ABAC |
| 4.10 | Content safety / PII classifiers | Todo | Often required in banking |

---

## 5. Backend — data plane (future)

| # | Task | Status | Notes |
|---|------|--------|--------|
| 5.1 | PostgreSQL schema (users, sessions, usage) | Todo | |
| 5.2 | Alembic migrations | Todo | |
| 5.3 | Redis (rate limits, semaphores, idempotency) | Todo | |
| 5.4 | Object storage for artifacts (optional) | Todo | MinIO / S3-compatible |

---

## 6. VS Code extension

| # | Task | Status | Notes |
|---|------|--------|--------|
| 6.1 | Extension activation + commands | Partial | Chat command done; explain is stub |
| 6.2 | Settings (`apiBaseUrl`, model, timeout, auth flag) | Done | `package.json` contributes |
| 6.3 | SecretStorage for bearer token | Partial | Read path; **no “Sign in” UX** yet |
| 6.4 | API client + SSE streaming parser | Done | `extension/src/api/client.ts` |
| 6.5 | Webview chat UI + streaming display | Done | `ChatPanelProvider` + `media/chat.js` |
| 6.6 | Explain selection → backend `/assist/explain` | Todo | Command placeholder only |
| 6.7 | Debug assist (Problems/diagnostics) | Todo | |
| 6.8 | Inline completions (optional product phase) | Todo | Higher latency + policy surface |
| 6.9 | `@vscode/test-electron` tests | Todo | |
| 6.10 | VSIX signing / marketplace packaging process | Todo | Enterprise usually private feed |

---

## 7. Infrastructure — containers & Kubernetes

| # | Task | Status | Notes |
|---|------|--------|--------|
| 7.1 | API Dockerfile (non-root) | Done | `infra/docker/backend.Dockerfile` |
| 7.2 | Docker Compose (API + Ollama) | Done | `infra/compose/docker-compose.yml` |
| 7.3 | Private registry push process | Todo | Org-specific |
| 7.4 | Helm chart (API) | Partial | `infra/helm/assistant-api/` starter |
| 7.5 | Helm chart (inference / GPU) | Todo | Separate from API |
| 7.6 | Ingress + TLS + annotations | Partial | Template exists; values org-specific |
| 7.7 | NetworkPolicies (default deny, allowlist) | Partial | Example policy; tune namespaces |
| 7.8 | PodSecurity / seccomp / restricted SCC | Partial | Values intent; cluster dependent |
| 7.9 | HPA / PDB / topology spread | Todo | After metrics baseline |
| 7.10 | GPU node selectors / taints | Todo | Inference chart |

---

## 8. CI/CD (air-gapped–ready)

| # | Task | Status | Notes |
|---|------|--------|--------|
| 8.1 | Lint + unit tests in CI | Todo | Add GitLab CI / Jenkinsfile |
| 8.2 | SAST (Semgrep/Sonar) | Todo | |
| 8.3 | Container build + push (digest tags) | Todo | |
| 8.4 | Cosign image signing | Todo | |
| 8.5 | Syft SBOM generation | Todo | |
| 8.6 | Offline promotion bundle (`docker save`, charts, SBOM) | Todo | Process doc + automation |

---

## 9. Observability & operations

| # | Task | Status | Notes |
|---|------|--------|--------|
| 9.1 | JSON logs to stdout | Partial | `structlog`; ship with Fluent Bit/DaemonSet |
| 9.2 | Prometheus metrics + RED dashboards | Todo | |
| 9.3 | GPU metrics (DCGM exporter) | Todo | Inference nodes |
| 9.4 | Tracing (OpenTelemetry) | Todo | |
| 9.5 | Runbooks (rotate secrets, model upgrade, incident) | Todo | |
| 9.6 | Synthetic probes / canary completions | Todo | |

---

## 10. Testing

| # | Task | Status | Notes |
|---|------|--------|--------|
| 10.1 | Backend unit tests | Partial | `tests/test_health.py` only |
| 10.2 | RBAC / JWT matrix tests | Todo | |
| 10.3 | Chat route tests (mocked LLM stream) | Todo | |
| 10.4 | Integration tests (Testcontainers Postgres later) | Todo | |
| 10.5 | k6 / Locust load tests (streaming) | Todo | |
| 10.6 | Security scanning in CI | Todo | |
| 10.7 | Helm chart tests (`helm unittest`) | Todo | |

---

## 11. RAG (future phase)

| # | Task | Status | Notes |
|---|------|--------|--------|
| 11.1 | Ingestion pipeline for approved corpora | Todo | |
| 11.2 | Embeddings service (local model) | Todo | |
| 11.3 | Vector store (`pgvector` / Milvus / Qdrant) | Todo | |
| 11.4 | Retrieval + citations in API + extension UX | Todo | |
| 11.5 | ACL on chunks (match RBAC) | Todo | |

---

## Summary — completed so far

**Strong progress (usable vertical slice for local dev):**

- FastAPI service with **streaming chat completions**, **optional JWT**, **RBAC hook on chat**, **audit fingerprints**, **Ollama + vLLM adapter stubs**, **health endpoints**, **Dockerfile + Compose**, **Helm starter**, **VS Code extension** with **webview chat** and **SSE client**.

**Partially done (needs hardening / productization):**

- JWT (**HS256 dev path**; needs **JWKS**, rotation, IdP integration).
- RBAC (minimal roles; expand + admin workflows).
- Audit (structured events; legal retention + SIEM mapping).
- Readiness checks (static).
- Extension **explain/debug** flows and **sign-in** UX.
- Helm **network policy / ingress** (templates exist; not tuned for your cluster).
- Devcontainer (present; not CI-validated).

**Not started (expected next waves):**

- **Database**, **Redis**, **rate limits**, **full CI/CD**, **signing/SBOM**, **observability stack**, **GPU inference chart**, **RAG**, **enterprise SSO/OIDC in extension**, **comprehensive tests**, **load tests**, **SAST/DAST**.

---

## Suggested next ten tasks (priority order)

1. **Integration tests** for `POST /api/v1/chat/completions` with **mocked httpx** stream (no GPU needed in CI).
2. **JWKS** JWT validation + config for issuer/audience + doc for token claims (`roles`).
3. Extension: **`assistant.setToken`** command or minimal **sign-in** using `SecretStorage` + test with `ASSISTANT_AUTH_ENABLED=true`.
4. Implement **`POST /api/v1/assist/explain`** + wire **explain selection** command end-to-end.
5. **Readiness** checks: optional Ollama `/api/tags` ping behind `ASSISTANT_READY_CHECK_INFERENCE`.
6. **CI pipeline** (lint, pytest, `npm run package`, `helm template` validation).
7. **Redis rate limiting** dependency + middleware (tenant/user keyed).
8. **PostgreSQL** + Alembic for usage counters / optional prompt metadata (policy-approved).
9. **Inference Helm chart** (GPU) + **NetworkPolicy** API → inference only.
10. **Observability**: Prometheus `/metrics` or OTel exporter + dashboards.

---

**Related docs:** `docs/IMPLEMENTATION_PLAN.md` (phased execution). Update **this file** when tasks move from Todo → Partial → Done.
