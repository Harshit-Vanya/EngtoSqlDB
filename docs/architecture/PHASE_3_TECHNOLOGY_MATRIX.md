# Phase 3 — Technology Decision Matrix

> **Principle**: No provider is locked in. Each placeholder represents an interface boundary.  
> The "Recommended" column reflects what would give the best portfolio/interview signal for a small team building in a short sprint. Final decisions are made by the team.

---

## 3.1 Core Infrastructure Placeholders

| # | Placeholder | Purpose | Options | Recommended | Reason |
|---|------------|---------|---------|-------------|--------|
| 1 | `<PRIMARY_DATABASE>` | Relational store for analytics data + application metadata | PostgreSQL, MySQL, SQL Server, CockroachDB | **PostgreSQL** | Rich SQL dialect, EXPLAIN support, JSON columns, excellent ecosystem, free, widely used in industry |
| 2 | `<VECTOR_DATABASE>` | Store and search embeddings for RAG | Qdrant, Weaviate, Pinecone, Milvus, pgvector (PostgreSQL extension), ChromaDB | **Qdrant** (prod) / **ChromaDB** (dev) | Qdrant: fast, self-hostable, filtering support. ChromaDB: zero-config for local dev. pgvector is viable for single-DB simplicity |
| 3 | `<LLM_PROVIDER>` | Text generation (SQL, explanation, intent) | OpenAI, Anthropic, Google Gemini, Azure OpenAI, local models (Ollama), Groq | **OpenAI GPT-4o** (primary) + **Ollama** (local dev) | GPT-4o: best SQL generation accuracy. Ollama: free local testing without API costs |
| 4 | `<EMBEDDING_PROVIDER>` | Text → vector embeddings | OpenAI text-embedding-3-small, Sentence Transformers (local), Cohere Embed, Voyage AI | **OpenAI text-embedding-3-small** (prod) / **Sentence Transformers** (local) | Good accuracy/cost ratio. Local model avoids API calls during development |
| 5 | `<OBJECT_STORAGE>` | Raw data files, exported results, pipeline artifacts | AWS S3, GCS, Azure Blob, MinIO (self-hosted) | **MinIO** (dev/local) | S3-compatible API; deploy anywhere. Production: use cloud-native equivalent |
| 6 | `<DATA_ORCHESTRATOR>` | Schedule and manage data pipeline DAGs | Apache Airflow, Dagster, Prefect, Temporal | **Dagster** | Modern asset-based approach, better testing story, easier local dev than Airflow, strong portfolio signal |
| 7 | `<CLOUD_PROVIDER>` | Production hosting, managed services | AWS, GCP, Azure, self-hosted | **Cloud-agnostic** (Docker-first) | Design for containers; deploy to any cloud. Use terraform with provider modules |
| 8 | `<CONTAINER_PLATFORM>` | Container orchestration | Kubernetes (EKS/GKE/AKS), Docker Compose, ECS, Cloud Run | **Docker Compose** (dev) / **Kubernetes** (prod) | Docker Compose for local dev; K8s manifests demonstrate production-readiness |
| 9 | `<AUTH_PROVIDER>` | User authentication, token management | Keycloak, Auth0, Firebase Auth, Supertokens, custom JWT | **Custom JWT** (MVP) + **Keycloak** (production) | Custom JWT: simple, no external deps for MVP. Keycloak: full OIDC, self-hosted, demonstrates enterprise auth |
| 10 | `<OBSERVABILITY_PLATFORM>` | Logs, metrics, traces | OpenTelemetry + Grafana stack (Loki/Prometheus/Tempo), Datadog, New Relic, ELK | **OpenTelemetry → Grafana stack** | Vendor-neutral (OTel), self-hostable, industry-standard, excellent interview talking point |
| 11 | `<SECRET_MANAGER>` | Secure credential storage | HashiCorp Vault, AWS Secrets Manager, Azure Key Vault, SOPS, dotenv (dev) | **dotenv** (dev) / **HashiCorp Vault** (prod) | .env for simplicity in dev; Vault shows security maturity |
| 12 | `<CI_CD_PLATFORM>` | Automated build, test, deploy | GitHub Actions, GitLab CI, Jenkins, CircleCI | **GitHub Actions** | Free tier, YAML-based, excellent ecosystem, most teams already use GitHub |
| 13 | `<CONTAINER_REGISTRY>` | Store Docker images | GHCR (GitHub), Docker Hub, ECR, GCR, Harbor | **GHCR (GitHub Container Registry)** | Integrated with GitHub Actions, free for public repos |

---

## 3.2 Application Framework Decisions

| # | Component | Options | Recommended | Reason |
|---|-----------|---------|-------------|--------|
| 14 | Backend Framework | FastAPI, Django REST, Flask, Litestar | **FastAPI** | Async-native, Pydantic integration, auto OpenAPI docs, type hints, best for AI services |
| 15 | SQL Parser | sqlglot, sqlparse, python-sqloxide, mo-sql-parsing | **sqlglot** | Multi-dialect support, AST manipulation, transpilation, actively maintained, pure Python |
| 16 | ORM / DB Toolkit | SQLAlchemy, Tortoise ORM, raw asyncpg | **SQLAlchemy 2.0** (async) | Industry standard, async support, migration via Alembic, rich query building |
| 17 | Agent Framework | LangGraph, LangChain, CrewAI, custom state machine | **Custom state machine** + optional LangGraph adapter | Custom gives full control + understanding for interviews; LangGraph adapter shows framework awareness |
| 18 | Frontend Framework | React, Vue, Svelte, Next.js | **React + Vite + TypeScript** | Largest ecosystem, most interview-relevant, fast with Vite |
| 19 | Charting Library | Recharts, Chart.js, Apache ECharts, Plotly | **Recharts** (React) | React-native, declarative, simple API, good defaults |
| 20 | HTTP Client (frontend) | Axios, fetch + TanStack Query, SWR | **TanStack Query** | Caching, retry, loading states built-in; modern React pattern |
| 21 | Testing (backend) | pytest, unittest | **pytest** + pytest-asyncio + pytest-cov | De facto standard, fixtures, parametrize, async support |
| 22 | Testing (frontend) | Vitest, Jest, React Testing Library | **Vitest + React Testing Library** | Fast (Vite-native), Jest-compatible API |
| 23 | Migrations | Alembic, Django migrations, Flyway | **Alembic** | Pairs with SQLAlchemy, autogenerate support |
| 24 | Task Queue (optional) | Celery, ARQ, RQ, Dramatiq | **ARQ** (if needed) | Async-native (asyncio), simple, uses Redis |
| 25 | Transformation Tool | dbt, SQLMesh, custom SQL | **dbt-core** | Industry standard for SQL transforms, testable, documented, great portfolio signal |

---

## 3.3 Development Tooling

| Tool | Purpose | Choice |
|------|---------|--------|
| Formatter | Code formatting | **Ruff** (format mode) |
| Linter | Static analysis | **Ruff** |
| Type Checker | Static type checking | **mypy** (strict mode) |
| Pre-commit | Git hooks | **pre-commit** framework |
| Env Management | Virtual environments | **uv** or **Poetry** |
| API Docs | Interactive docs | FastAPI built-in (Swagger + ReDoc) |
| Makefile | Developer commands | GNU Make |

---

## 3.4 Decision Criteria Rationale

Each recommendation was evaluated on:

1. **Portfolio Signal** — Does it demonstrate industry-relevant skills?
2. **Team Velocity** — Can a 4-person team ship in a short sprint?
3. **Interview Depth** — Can each team member explain WHY this choice was made?
4. **Self-Hostable** — Can it run locally without cloud accounts?
5. **Replaceability** — Is it behind an abstraction so it can be swapped?

---

## 3.5 Provider Swap Examples

To demonstrate the abstraction works, here's how swapping would look:

```python
# Swap LLM Provider: OpenAI → Anthropic
# Only change: backend/app/infrastructure/llm/adapter.py

# Before (OpenAI)
class OpenAIAdapter(LLMProvider):
    async def generate(self, prompt: str, **kwargs) -> LLMResponse:
        response = await self.client.chat.completions.create(...)
        return LLMResponse(text=response.choices[0].message.content, ...)

# After (Anthropic)
class AnthropicAdapter(LLMProvider):
    async def generate(self, prompt: str, **kwargs) -> LLMResponse:
        response = await self.client.messages.create(...)
        return LLMResponse(text=response.content[0].text, ...)

# Zero changes to: agents/, services/, sql/, rag/, api/
```

```python
# Swap Vector Store: Qdrant → pgvector
# Only change: backend/app/infrastructure/vector_store/adapter.py

# The rest of the application calls:
#   await vector_store.search(embedding, top_k=5)
# ...and doesn't know or care which store is behind it.
```

---

## 3.6 Cost Considerations (Development Phase)

| Resource | Free Tier / Self-Hosted | Estimated Monthly Cost (dev) |
|----------|------------------------|------------------------------|
| PostgreSQL | Docker (self-hosted) | $0 |
| Qdrant / ChromaDB | Docker (self-hosted) | $0 |
| OpenAI API | Pay-per-use | ~$10-30 (development queries) |
| MinIO | Docker (self-hosted) | $0 |
| GitHub Actions | 2000 min/month free | $0 |
| Dagster | OSS / local | $0 |
| Grafana Stack | Docker (self-hosted) | $0 |

**Total estimated dev cost: ~$10-30/month** (primarily LLM API calls)

Tip: Use Ollama with a local model (e.g., CodeLlama, Mistral) for development to reduce costs to $0.
