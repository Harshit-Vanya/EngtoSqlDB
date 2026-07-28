# Phase 9 — Team Task Breakdown

## 9.1 Team Structure

| Team | Focus Area | Developer |
|------|-----------|-----------|
| **Dev A** | AI / LLM / Agents / RAG | AI/ML Engineer |
| **Dev B** | Database / Data Engineering / Pipeline | Data Engineer |
| **Dev C** | FastAPI / SQL Validation / Security | Backend Engineer |
| **Dev D** | Frontend / Docker / CI/CD / Docs | Full-Stack / DevOps |

---

## 9.2 Dependency Graph

```mermaid
graph TD
    subgraph "Foundation (Week 1 - All Teams)"
        F1[Core config + types + exceptions]
        F2[Infrastructure protocol interfaces]
        F3[Docker Compose base setup]
        F4[Database migrations + seed data]
    end

    subgraph "Dev A: AI Layer"
        A1[LLM Provider adapter]
        A2[Embedding Provider adapter]
        A3[Intent Detector agent]
        A4[SQL Generator agent]
        A5[Self-Correction agent]
        A6[Explanation agent]
        A7[RAG: indexer + retriever]
        A8[Prompt templates]
        A9[Visualization recommender]
    end

    subgraph "Dev B: Data Layer"
        B1[Analytics DB schema + seed data]
        B2[Schema metadata catalog]
        B3[Business glossary + metrics definitions]
        B4[Data pipeline: ingestion + transforms]
        B5[dbt models]
        B6[Schema indexing into vector store]
        B7[Data quality checks]
    end

    subgraph "Dev C: API + Security Layer"
        C1[FastAPI app skeleton + middleware]
        C2[Auth service (JWT + API keys)]
        C3[RBAC permission engine]
        C4[SQL Validator (sqlglot)]
        C5[Security checker]
        C6[Cost analyzer (EXPLAIN)]
        C7[Query executor]
        C8[Query orchestrator (state machine)]
        C9[Rate limiting]
    end

    subgraph "Dev D: Frontend + DevOps"
        D1[React project setup]
        D2[API client + auth hooks]
        D3[Query input + results UI]
        D4[Visualization component]
        D5[Docker multi-service compose]
        D6[CI/CD pipeline (GitHub Actions)]
        D7[Documentation]
        D8[E2E test setup]
    end

    F1 --> A1
    F1 --> C1
    F2 --> A1
    F2 --> A2
    F2 --> C7
    F3 --> D5
    F4 --> B1

    A1 --> A3
    A1 --> A4
    A1 --> A5
    A1 --> A6
    A2 --> A7
    A3 --> C8
    A4 --> C8
    A5 --> C8
    A7 --> C8

    B1 --> B2
    B2 --> B3
    B2 --> B6
    B6 --> A7

    C1 --> C2
    C2 --> C3
    C3 --> C5
    C4 --> C8
    C5 --> C8
    C6 --> C8
    C7 --> C8

    C8 --> D3
    D1 --> D2
    D2 --> D3
    D3 --> D4
```

---

## 9.3 Dev A — AI / LLM / Agents / RAG

### Task List

| # | Task | Dependencies | Expected Output | Est. Hours |
|---|------|-------------|-----------------|:----------:|
| A1 | LLM Provider abstraction + adapter | Core config, Protocol interfaces | `infrastructure/llm/base.py`, `adapter.py` | 4 |
| A2 | Embedding Provider abstraction + adapter | Core config, Protocol interfaces | `infrastructure/embedding/base.py`, `adapter.py` | 3 |
| A3 | Prompt templates (all 5: intent, generation, correction, explanation, visualization) | None | `prompts/*.py` | 6 |
| A4 | Intent Detector agent | A1, A3 | `agents/intent_detector.py` + unit tests | 5 |
| A5 | SQL Generator agent | A1, A3 | `agents/sql_generator.py` + unit tests | 6 |
| A6 | Self-Correction agent | A1, A3, A5 | `agents/self_correction.py` + unit tests | 5 |
| A7 | Explanation Generator agent | A1, A3 | `agents/explanation.py` + unit tests | 4 |
| A8 | Visualization Recommender (rules + LLM fallback) | A1, A3 | `visualization/recommender.py`, `rules.py` + tests | 5 |
| A9 | RAG: Chunker + Indexer | A2, B6 schema data | `rag/chunker.py`, `rag/indexer.py` + tests | 5 |
| A10 | RAG: Retriever + Context Builder | A2, A9, Vector store adapter | `rag/retriever.py`, `rag/context_builder.py` + tests | 6 |
| A11 | RAG: Re-ranker | A10 | `rag/ranker.py` + tests | 3 |
| A12 | Vector Store adapter | Protocol interfaces | `infrastructure/vector_store/adapter.py` | 3 |
| A13 | Integration tests (full agent chain) | A4-A11, mock DB | Integration test suite | 4 |

**Total estimated: ~59 hours**

### Key Interfaces Produced
- `LLMProvider` adapter (used by C8, A4-A8)
- `EmbeddingProvider` adapter (used by A9, A10)
- `VectorStore` adapter (used by A10, B6)
- All agent classes (consumed by C8 orchestrator)

---

## 9.4 Dev B — Database / Data Engineering / Pipeline

### Task List

| # | Task | Dependencies | Expected Output | Est. Hours |
|---|------|-------------|-----------------|:----------:|
| B1 | Analytics DB schema design + SQL scripts | None | `data_pipeline/seeds/schema.sql` | 4 |
| B2 | Sample data generation (CSVs: 1K customers, 10K orders, etc.) | B1 | `data_pipeline/seeds/sample_data/*.csv` | 5 |
| B3 | Database seed script (load CSVs → DB) | B1, B2 | `data_pipeline/seeds/seed_database.py` | 3 |
| B4 | Schema metadata catalog tables (app DB) | Alembic setup from C1 | Migration for schema_metadata, business_glossary, etc. | 4 |
| B5 | Schema metadata population script | B1, B4 | `data_pipeline/schema_catalog/catalog.py` | 4 |
| B6 | Business glossary + metric definitions (YAML) | Domain knowledge | `data_pipeline/schema_catalog/definitions/*.yaml` | 5 |
| B7 | Schema → Vector Store indexing script | B5, B6, A12 vector store adapter | `data_pipeline/schema_catalog/indexer.py` | 5 |
| B8 | dbt project: staging models | B1 | `dbt/models/staging/stg_*.sql` | 4 |
| B9 | dbt project: intermediate + marts models | B8 | `dbt/models/intermediate/`, `dbt/models/marts/` | 5 |
| B10 | dbt tests (schema tests, data tests) | B8, B9 | `dbt/tests/` | 3 |
| B11 | Data pipeline: ingestion module | B1 | `data_pipeline/ingestion/` | 4 |
| B12 | Data pipeline: quality checks | B11 | `data_pipeline/quality/checks.py` | 3 |
| B13 | DAG definitions (for orchestrator) | B11, B12 | `data_pipeline/orchestration/dags/` | 4 |
| B14 | Example NL→SQL pairs (for RAG) | B1, domain knowledge | `data_pipeline/schema_catalog/definitions/examples.yaml` | 4 |
| B15 | Evaluation benchmark questions (100) | B1, B2 (needs data to verify) | `evaluation/benchmark_questions.json` | 6 |

**Total estimated: ~63 hours**

### Key Interfaces Produced
- Analytics database (schema + data) — used by C7 executor, A10 retriever
- Schema metadata in app DB — used by C8 orchestrator
- Vector store populated with schema embeddings — used by A10 retriever
- YAML definitions — used by A9 indexer
- Benchmark dataset — used by evaluation runner

---

## 9.5 Dev C — FastAPI / SQL Validation / Security

### Task List

| # | Task | Dependencies | Expected Output | Est. Hours |
|---|------|-------------|-----------------|:----------:|
| C1 | FastAPI app skeleton (main.py, dependencies, router structure) | Core config | `app/main.py`, `api/router.py`, `api/v1/*.py` stubs | 4 |
| C2 | Core config + types + exceptions | None (DAY 1) | `core/config.py`, `core/types.py`, `core/exceptions.py` | 3 |
| C3 | Pydantic request/response schemas | API design doc | `schemas/request/*.py`, `schemas/response/*.py` | 4 |
| C4 | Auth middleware + JWT service | C1, C2 | `api/middleware/auth.py`, `services/auth_service.py` | 6 |
| C5 | User + Role ORM models + Alembic migration | C2 | `models/user.py`, `models/permission.py`, migration | 4 |
| C6 | RBAC permission engine | C4, C5 | `security/rbac.py`, `security/permission_checker.py` | 6 |
| C7 | SQL Validator (sqlglot-based) | C2 | `sql/validator.py`, `sql/parser.py` + unit tests | 6 |
| C8 | SQL Sanitizer (injection prevention) | C7 | `security/sql_sanitizer.py` + unit tests | 4 |
| C9 | Cost Analyzer (EXPLAIN integration) | C2, DB adapter | `sql/cost_analyzer.py` + unit tests | 4 |
| C10 | Query Executor (read-only, timeout, max_rows) | C2, DB adapter | `sql/executor.py` + unit tests | 4 |
| C11 | Result Processor | C10 | `services/result_processor.py` + tests (in services or dedicated) | 3 |
| C12 | Database adapter (SQLAlchemy async) | Protocol interfaces | `infrastructure/database/adapter.py`, `session.py` | 4 |
| C13 | Query Orchestrator (state machine) | A4-A8 agents, C7-C11 | `services/query_orchestrator.py` + integration tests | 8 |
| C14 | Query history service + ORM model | C5, C12 | `services/history_service.py`, `models/query_record.py` | 3 |
| C15 | Rate limiting middleware | C1 | `api/middleware/rate_limit.py` | 3 |
| C16 | API endpoints (all routes wired) | C3, C4, C13, C14 | `api/v1/query.py`, `api/v1/schema.py`, etc. — full implementation | 5 |
| C17 | Error handlers + standardized responses | C1, C3 | `api/errors/handlers.py`, `api/errors/responses.py` | 2 |
| C18 | Observability: structured logging + metrics | C2 | `infrastructure/observability/*.py` | 4 |
| C19 | Audit logging | C4, C6 | `security/audit.py` | 3 |

**Total estimated: ~80 hours**

### Key Interfaces Produced
- Full FastAPI application (the backbone everything connects to)
- Query Orchestrator (integrates all of Dev A's agents)
- SQL validation + security pipeline
- Auth + RBAC system
- Database adapters (used by A10, B7)

---

## 9.6 Dev D — Frontend / Docker / CI/CD / Documentation

### Task List

| # | Task | Dependencies | Expected Output | Est. Hours |
|---|------|-------------|-----------------|:----------:|
| D1 | React + Vite + TypeScript project setup | None | `frontend/` scaffolded with routing, state, types | 3 |
| D2 | API client (typed fetch wrapper) | API design doc | `frontend/src/services/api.ts` | 3 |
| D3 | Auth flow (login page + token management) | D1, D2, C4 auth API | `frontend/src/pages/Login.tsx`, `hooks/useAuth.ts` | 4 |
| D4 | Query Input component | D1 | `frontend/src/components/QueryInput/` | 3 |
| D5 | Results Table component | D1 | `frontend/src/components/ResultsTable/` | 3 |
| D6 | SQL Viewer component (syntax highlighting) | D1 | `frontend/src/components/SQLViewer/` | 2 |
| D7 | Visualization component (Recharts) | D1 | `frontend/src/components/Visualization/` | 5 |
| D8 | Explanation Card component | D1 | `frontend/src/components/ExplanationCard/` | 2 |
| D9 | Query Page (main page, integrates D4-D8) | D4-D8, D2 | `frontend/src/pages/QueryPage.tsx` | 4 |
| D10 | History Page | D2 | `frontend/src/pages/HistoryPage.tsx` | 3 |
| D11 | Schema Explorer page | D2 | `frontend/src/pages/SchemaPage.tsx` | 3 |
| D12 | Docker Compose: full local stack | B1 (DB), A12 (vector store) | `docker/docker-compose.yml` | 4 |
| D13 | Backend Dockerfile | C1 | `backend/Dockerfile` | 2 |
| D14 | Frontend Dockerfile | D1 | `frontend/Dockerfile` | 2 |
| D15 | CI pipeline: lint + test + build | C2 (tests exist) | `.github/workflows/ci.yml` | 4 |
| D16 | CD pipeline: Docker build + push | D13, D14, D15 | `.github/workflows/cd.yml` | 3 |
| D17 | Setup scripts (dev environment) | D12 | `scripts/setup_dev.sh`, `scripts/seed_data.sh` | 2 |
| D18 | README + Development guide | All teams | `README.md`, `docs/guides/DEVELOPMENT.md` | 3 |
| D19 | API documentation (OpenAPI export) | C16 | FastAPI auto-docs + `docs/api/` | 1 |
| D20 | E2E test setup (Playwright or similar) | D9, C16 | `tests/e2e/` | 4 |
| D21 | Makefile (common commands) | D12 | `Makefile` | 1 |

**Total estimated: ~61 hours**

### Key Interfaces Produced
- Complete frontend application
- Docker infrastructure (everyone uses this for local dev)
- CI/CD pipelines
- Documentation
- E2E tests

---

## 9.7 Shared / Day-1 Tasks (All Devs)

These tasks should be completed first to unblock parallel work:

| Task | Owner | Day | Purpose |
|------|-------|:---:|---------|
| Git repo setup, branch strategy, .gitignore | Dev D | Day 1 | Collaboration infrastructure |
| Core config + types + exceptions | Dev C | Day 1 | All modules depend on this |
| Protocol interfaces (LLM, Embedding, VectorStore, DB, Auth) | Dev C + Dev A | Day 1 | All adapters implement these |
| Docker Compose (PostgreSQL + vector store containers) | Dev D | Day 1 | Everyone needs running services |
| Analytics DB schema SQL | Dev B | Day 1 | Needed for validation, execution, testing |
| pyproject.toml + requirements | Dev C | Day 1 | Dependency management |

---

## 9.8 Integration Points (Cross-Team Coordination)

| Integration | Teams | Contract | Coordination Needed |
|-------------|-------|----------|-------------------|
| Agents → Orchestrator | A + C | Agent base class + I/O dataclasses | Agree on interface Day 1 |
| Schema indexer → Vector store | B + A | Vector store adapter + document format | Agree on embedding schema Day 2 |
| API → Frontend | C + D | OpenAPI spec (auto-generated) | API contract review Day 2 |
| Orchestrator → All agents | C + A | State machine transitions + agent registry | Integration test Day 4 |
| Docker → All services | D + All | Port assignments, env vars, health checks | Docker compose review Day 1 |
| Evaluation → Full pipeline | B (data) + All | Benchmark format + test database | E2E integration Day 5 |

---

## 9.9 Sprint Timeline (Suggested)

```text
Day 1-2:  Foundation (all devs: interfaces, config, Docker, DB schema)
Day 3-5:  Core modules (each dev works on their primary modules)
Day 6-7:  Integration (wire agents → orchestrator → API → frontend)
Day 8:    Testing + bug fixes
Day 9:    Evaluation run + documentation
```

This is aggressive but achievable if interfaces are agreed upon Day 1 and each developer can work independently on their modules.
